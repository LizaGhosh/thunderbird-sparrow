"""
Voice Recording and Transcription Module
Uses OpenAI Whisper for speech-to-text conversion
"""

import os
import tempfile
import wave
import pyaudio
import whisper
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceRecorder:
    """Voice recording and transcription using OpenAI Whisper"""
    
    def __init__(self, model_name="base"):
        """
        Initialize the voice recorder
        
        Args:
            model_name (str): Whisper model size (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.audio = pyaudio.PyAudio()
        self.whisper_model = None
        self.sample_rate = 16000
        self.channels = 1
        self.chunk = 1024
        self.format = pyaudio.paInt16
        
        # Debug: List available audio devices
        self._list_audio_devices()
        
    def _list_audio_devices(self):
        """List all available audio input devices for debugging"""
        logger.info("=== Available Audio Input Devices ===")
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:  # Input device
                logger.info(f"Device {i}: {device_info['name']}")
                logger.info(f"  - Max Input Channels: {device_info['maxInputChannels']}")
                logger.info(f"  - Sample Rate: {device_info['defaultSampleRate']}")
                logger.info(f"  - Is Default: {device_info['index'] == self.audio.get_default_input_device_info()['index']}")
        logger.info("=====================================")
        
    def _check_audio_levels(self, frames):
        """Check if recorded audio has actual content"""
        if not frames:
            logger.warning("No audio frames recorded!")
            return
            
        # Convert frames to audio data and check levels
        import numpy as np
        
        try:
            # Convert bytes to 16-bit integers
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            
            # Calculate audio statistics
            max_level = np.max(np.abs(audio_data))
            rms_level = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
            
            logger.info(f"Audio levels - Max: {max_level}, RMS: {rms_level:.2f}")
            
            # Check if audio is mostly silence
            silence_threshold = 100  # Adjust this value as needed
            if max_level < silence_threshold:
                logger.warning(f"Audio appears to be mostly silence (max level: {max_level})")
                logger.warning("Check microphone permissions and input levels")
            else:
                logger.info(f"Audio levels look good (max level: {max_level})")
                
        except Exception as e:
            logger.error(f"Failed to analyze audio levels: {e}")
        
    def test_microphone(self, duration=3):
        """Test microphone with a short recording to check levels"""
        logger.info("=== Testing Microphone ===")
        try:
            # Test recording
            test_path = self.record_audio(duration=duration)
            
            # Check file size
            import os
            file_size = os.path.getsize(test_path)
            logger.info(f"Test recording file size: {file_size} bytes")
            
            if file_size < 1000:  # Very small file
                logger.warning("Test recording file is very small - possible permission issue")
            
            # Clean up test file
            try:
                os.remove(test_path)
                logger.info("Test recording cleaned up")
            except:
                pass
                
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
        
    def load_whisper_model(self):
        """Load the Whisper model (lazy loading)"""
        if self.whisper_model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.whisper_model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded successfully")
        return self.whisper_model
    
    def record_audio(self, duration=10, save_path=None):
        """
        Record audio for a specified duration
        
        Args:
            duration (int): Recording duration in seconds
            save_path (str): Optional path to save the audio file
            
        Returns:
            str: Path to the recorded audio file
        """
        if save_path is None:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(temp_dir, f"voice_recording_{timestamp}.wav")
        
        logger.info(f"Starting audio recording for {duration} seconds...")
        
        # Open audio stream with better error handling
        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            logger.info(f"Audio stream opened successfully")
            logger.info(f"Recording format: {self.format}, Channels: {self.channels}, Rate: {self.sample_rate}")
            
        except Exception as e:
            logger.error(f"Failed to open audio stream: {e}")
            raise
        
        frames = []
        total_frames = int(self.sample_rate / self.chunk * duration)
        logger.info(f"Will record {total_frames} frames over {duration} seconds")
        
        try:
            # Record audio with progress logging
            for i in range(total_frames):
                data = stream.read(self.chunk, exception_on_overflow=False)
                frames.append(data)
                
                # Log progress every second
                if i % int(self.sample_rate / self.chunk) == 0:
                    seconds_recorded = i // int(self.sample_rate / self.chunk)
                    logger.info(f"Recording... {seconds_recorded}/{duration} seconds")
                
        except KeyboardInterrupt:
            logger.info("Recording stopped by user")
        except Exception as e:
            logger.error(f"Recording error: {e}")
            raise
        finally:
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            logger.info(f"Audio stream closed. Recorded {len(frames)} frames")
        
        # Save the recorded audio
        with wave.open(save_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
        
        # Debug: Check audio levels
        self._check_audio_levels(frames)
        
        logger.info(f"Audio saved to: {save_path}")
        return save_path
    
    def transcribe_audio(self, audio_path):
        """
        Transcribe audio using OpenAI Whisper
        
        Args:
            audio_path (str): Path to the audio file
            
        Returns:
            dict: Transcription result with text and metadata
        """
        logger.info(f"Transcribing audio: {audio_path}")
        
        try:
            # Load model if not already loaded
            model = self.load_whisper_model()
            
            # Transcribe audio
            result = model.transcribe(audio_path)
    
            transcription = {
                'text': result['text'].strip(),
                'language': result.get('language', 'unknown'),
                'segments': result.get('segments', []),
                'audio_path': audio_path,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Transcription completed: {len(transcription['text'])} characters")
            return transcription
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    def cleanup(self):
        """Clean up resources"""
        if self.audio:
            self.audio.terminate()
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

def create_voice_recorder(model_name="base"):
    """
    Factory function to create a voice recorder instance
    
    Args:
        model_name (str): Whisper model size
        
    Returns:
        VoiceRecorder: Configured voice recorder instance
    """
    return VoiceRecorder(model_name)
