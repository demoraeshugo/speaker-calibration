/**
 * @class provides a simple interface for recording audio from a microphone
 * using the Media Recorder API.
 */
class AudioRecorder {
  /** @private */
  #mediaRecorder;

  /** @private */
  #recordedChunks = [];

  /** @private */
  #audioBlob;

  /** @private */
  #audioContext;

  /** @private */
  #fileReader;

  /** @private */
  #arrayBuffer;

  /** @private */
  #recordedSignals = [];

  /**
   * creates a new AudioRecorder instance.
   * Sets up the audio context and file reader.
   */
  constructor() {
    this.#audioContext = new (window.AudioContext ||
      window.webkitAudioContext ||
      window.audioContext)();
    this.#fileReader = new FileReader();
  }

  #saveRecording = async () => {
    this.#arrayBuffer = await this.#audioBlob.arrayBuffer();

    // Convert array buffer into audio buffer
    await this.#audioContext.decodeAudioData(this.#arrayBuffer, audioBuffer => {
      // Do something with audioBuffer
      // TODO: Address the fact that the audio buffer is being continously filled,
      // we want a new buffer each round.
      const data = audioBuffer.getChannelData(0);
      console.log(data);
      this.#recordedSignals.push(data);
    });
  };

  /**
   * Event listener triggered when data is available in the media recorder.
   * @private
   * @param {*} e - The event object.
   */
  #onRecorderDataAvailable = e => {
    if (e.data && e.data.size > 0) this.#recordedChunks.push(e.data);
  };

  /**
   * Event listener triggered when the media recorder stops recording.
   * @private
   */
  #onRecorderStop = () => {
    // Create a blob from the recorded audio chunks
    this.#audioBlob = new Blob(this.#recordedChunks, {
      type: 'audio/webm;codecs=opus',
    });
  };

  /**
   * Method to create a media recorder object and set up event listeners.
   * @private
   * @param {MediaStream} stream - The stream of audio from the Listener.
   */
  #setMediaRecorder = stream => {
    // Create a new MediaRecorder object
    this.#mediaRecorder = new MediaRecorder(stream);

    // Add event listeners
    this.#mediaRecorder.ondataavailable = e => this.#onRecorderDataAvailable(e);
  };

  /**
   * Public method to start the recording process.
   * @param {MediaStream} stream - The stream of audio from the Listener.
   */
  startRecording = stream => {
    // Set up media recorder if needed
    if (!this.#mediaRecorder) this.#setMediaRecorder(stream);
    this.#recordedChunks = [];
    this.#mediaRecorder.start();
  };

  /**
   * Method to stop the recording process.
   * @public
   */
  stopRecording = async () => {
    // Stop the media recorder, and wait for the data to be available
    await new Promise(resolve => {
      this.#mediaRecorder.onstop = () => {
        // when the stop event is triggered, resolve the promise
        this.#audioBlob = new Blob(this.#recordedChunks, {
          type: 'audio/webm;codecs=opus',
        });
        resolve(this.#audioBlob);
      };
      // call stop
      this.#mediaRecorder.stop();
    });
    // Now that we have data, save it
    await this.#saveRecording();
  };

  getRecordedSignal = () => this.#recordedSignals[this.#recordedSignals.length - 1];
}

export default AudioRecorder;
