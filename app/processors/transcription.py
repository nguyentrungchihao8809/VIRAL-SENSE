import logging
import os
from typing import Optional, Dict, Any
from faster_whisper import WhisperModel
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class TranscriptionProcessor:
    """Sử dụng faster-whisper để chuyển đổi âm thanh thành văn bản an toàn trong môi trường bất đồng bộ"""
    
    def __init__(self, model_size: str = "base", compute_type: str = "int8"):
        """
        Khởi tạo bộ cấu hình mô hình Whisper
        """
        self.model_size = model_size
        self.compute_type = compute_type
        self.model = None
        # Khởi tạo Executor giới hạn luồng tính toán nặng
        self.executor = ThreadPoolExecutor(max_workers=2)
        # Khóa Lock để đảm bảo tại một thời điểm chỉ có duy nhất 1 luồng được quyền khởi tạo nạp model vào RAM
        self._init_lock = asyncio.Lock()
        
    async def initialize_model(self):
        """Khởi tạo mô hình (Thread-safe & Async-safe)"""
        if self.model is not None:
            return

        async with self._init_lock:
            # Kiểm tra lại một lần nữa sau khi đoạt được khóa Lock đề phòng luồng khác đã init xong
            if self.model is None:
                logger.info(f"⚙️ Đang tiến hành nạp mô hình Whisper ({self.model_size}, {self.compute_type}) vào bộ nhớ...")
                loop = asyncio.get_running_loop()
                
                # Nạp model chạy ngầm trong Executor, chỉ định thư mục cache tránh Docker pull lại liên tục
                self.model = await loop.run_in_executor(
                    self.executor,
                    lambda: WhisperModel(
                        model_size_or_path=self.model_size,
                        device="cpu",  # Ép chạy CPU theo kiến trúc hiện tại, đổi thành "cuda" nếu có GPU
                        compute_type=self.compute_type,
                        download_root="/app/models_cache/whisper"
                    )
                )
                logger.info(f"✓ Mô hình Whisper ({self.model_size}, {self.compute_type}) đã load thành công.")
    
    async def transcribe(
        self, 
        audio_path: str,
        language: str = "vi"
    ) -> Optional[Dict[str, Any]]:
        """
        Chuyển đổi tệp âm thanh thành văn bản
        """
        if not os.path.exists(audio_path):
            logger.error(f"❌ Tệp âm thanh không tồn tại: {audio_path}")
            return None
        
        try:
            # Đảm bảo mô hình được nạp an toàn trước khi bóc băng
            await self.initialize_model()
            
            # Gọi tiến trình xử lý nặng tính toán trích xuất âm thanh trong Thread riêng
            loop = asyncio.get_running_loop()
            segments_list, detected_info = await loop.run_in_executor(
                self.executor,
                self._run_transcription,
                audio_path,
                language
            )
            
            # Tập hợp các đoạn segments thành văn bản hoàn chỉnh
            full_text = " ".join([segment["text"] for segment in segments_list]).strip()
            
            # Trả về định dạng khớp 100% với mong đợi từ file tasks.py của bạn
            result = {
                "text": full_text,
                "segments": segments_list,
                "detected_language": detected_info.language,
                "language_probability": float(detected_info.language_probability) if hasattr(detected_info, 'language_probability') else None
            }
            
            logger.info(f"✓ Transcribe thành công file: {audio_path}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Lỗi xảy ra trong quá trình transcribe: {str(e)}", exc_info=True)
            return None
    
    def _run_transcription(self, audio_path: str, language: str):
        """Hàm chạy transcription (chạy trong executor thread) đã sửa hoàn toàn lỗi typo"""
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            best_of=5,
            temperature=0.0,
            compression_ratio_threshold=2.4,
            
            # --- ĐÃ SỬA CHÍNH XÁC THAM SỐ CHỐNG LẶP TỪ TẠI ĐÂY ---
            no_speech_threshold=0.5,      # Đoạn nào > 50% là tạp âm hoặc nhạc thì bỏ qua
            repetition_penalty=1.2,       # Đã sửa typo: phạt nặng nếu từ ngữ bị lặp đi lặp lại
            condition_on_previous_text=False # KHÔNG bắt chước văn cảnh đoạn trước để tránh lặp chuỗi
        )
        
        processed_segments = []
        for i, segment in enumerate(segments):
            text_clean = segment.text.strip()
            if not text_clean:
                continue
                
            processed_segments.append({
                "id": i,
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text_clean,
                "confidence": round(segment.confidence, 4) if hasattr(segment, 'confidence') and segment.confidence else None
            })
            
        return processed_segments, info

    async def transcribe_batch(
        self,
        audio_paths: list,
        language: str = "vi"
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """Transcribe nhiều tệp âm thanh cùng lúc theo cơ chế hàng đợi bất đồng bộ"""
        tasks = [
            self.transcribe(path, language)
            for path in audio_paths
        ]
        results = await asyncio.gather(*tasks)
        return {
            path: result
            for path, result in zip(audio_paths, results)
        }

    def cleanup(self):
        """Giải phóng tài nguyên bộ nhớ hệ thống"""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("✓ Transcription processor đã cleanup giải phóng tài nguyên hoàn tất.")
        

        # --- ĐOẠN CODE DÙNG ĐỂ TEST NHANH (MÁY LOCAL HOẶC TRONG CONTAINER) ---
if __name__ == "__main__":
    import time
    
    # Thiết lập log hiển thị ra console để theo dõi tiến trình
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    async def main_test():
        # 1. Khởi tạo class
        processor = TranscriptionProcessor(model_size="base", compute_type="int8")
        
        # 2. Bạn hãy chuẩn bị sẵn 1 file âm thanh ngắn (.mp3 hoặc .wav) ở máy của bạn
        # Ví dụ mình để một file test.mp3 ngay tại thư mục gốc của dự án
        audio_test_path = "test.mp4" 
        
        if not os.path.exists(audio_test_path):
            print(f"\n❌ [LỖI TEST]: Bạn ơi, hãy bỏ 1 file audio tên là '{audio_test_path}' vào thư mục để test nhé!")
            return

        print("\n🚀 --- BẮT ĐẦU CHẠY THỬ MÔ HÌNH WHISPER ---")
        start_time = time.time()
        
        # 3. Kích hoạt bóc băng
        result = await processor.transcribe(audio_test_path, language="vi")
        
        end_time = time.time()
        print(f"⏱️ Thời gian xử lý: {end_time - start_time:.2f} giây")
        
        # 4. In kết quả ra màn hình
        if result:
            print("\n✅ KẾT QUẢ TRÍCH XUẤT THÀNH CÔNG:")
            print(f"📌 Ngôn ngữ hệ thống đoán: {result['detected_language']} ({result['language_probability']*100:.1f}%)")
            print(f"📝 Văn bản thô thu được:\n\"{result['text']}\"")
            print(f"\n📊 Chi tiết các mốc thời gian (Segments Count): {len(result['segments'])} đoạn.")
        else:
            print("\n❌ KẾT QUẢ: Thất bại, kiểm tra lại log lỗi ở trên.")
            
        # Giải phóng tài nguyên
        processor.cleanup()

    # Chạy hàm async test
    asyncio.run(main_test())