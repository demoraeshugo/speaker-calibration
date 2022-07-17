window.onload = () => {
  const flexSwitchCheckIR = document.getElementById('flexSwitchCheckIR');
  const flexSwitchCheckVolume = document.getElementById('flexSwitchCheckVolume');
  const previousCaptureCSV = document.getElementById('previous-capture-csv');
  const iirCSV = document.getElementById('iir-csv');
  const sendToServerButton = document.getElementById('sendToServerButton');

  const {Speaker, VolumeCalibration, ImpulseResponseCalibration} = speakerCalibrator;

  const normalize = (min, max) => {
    var delta = max - min;
    return val => {
      return (val - min) / delta;
    };
  };

  const useIRResult = async invertedIR => {
    // invertedIRNorm = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1];
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    const audioCtx = new AudioContext();
    const invertedIRNorm = invertedIR;
    const audioFileName = 'Queen-Bohemian_Rhapsody.wav';
    const audioFileURL = window.location.hostname.includes('localhost')
      ? '../example/' + audioFileName
      : './' + audioFileName;
    const audioFile = fetch(audioFileURL)
      .then(response => response.arrayBuffer())
      .then(buffer => audioCtx.decodeAudioData(buffer))
      .then(async buffer => {
        buffer.channelCount = 1;
        buffer.numberOfChannels = 1;
        const track = audioCtx.createBufferSource(1, buffer.length, audioCtx.sampleRate);
        track.buffer = buffer;
        track.channelCount = 1;

        const myArrayBuffer = audioCtx.createBuffer(1, invertedIRNorm.length, audioCtx.sampleRate);

        // Fill the buffer with white noise;
        // just random values between -1.0 and 1.0
        // This gives us the actual ArrayBuffer that contains the data
        const nowBuffering = myArrayBuffer.getChannelData(0);
        for (let i = 0; i < myArrayBuffer.length; i++) {
          // Math.random() is in [0; 1.0]
          // audio needs to be in [-1.0; 1.0]
          nowBuffering[i] = invertedIRNorm[i];
        }

        const convolver = audioCtx.createConvolver();
        convolver.normalize = false;
        convolver.channelCount = 1;
        convolver.buffer = myArrayBuffer;

        track.connect(convolver);
        convolver.connect(audioCtx.destination);
        track.start();
      });
  };

  const handlePreviousCaptureUpload = e => {
    const calibratorParams = {
      numCaptures: 0,
      numMLSPerCapture: 0,
      download: false,
    };

    const f = e.target.files[0];
    if (f) {
      e.preventDefault();
      const reader = new FileReader();

      reader.onload = async e => {
        console.log('Hello World');
        const text = e.target.result;
        const testIRCalibration = new ImpulseResponseCalibration(calibratorParams);

        const handleImpulseResponsEvent = data => {
          if (data.res) {
            testIRCalibration.sendImpulseResponsesToServerForProcessing();
          }
        };

        const handleInvertedImpulseResponseEvent = async data => {
          if (data.res) {
            await useIRResult(testIRCalibration.invertedImpulseResponse);
          }
        };

        testIRCalibration.on('ImpulseResponse', handleImpulseResponsEvent);
        testIRCalibration.on('InvertedImpulseResponse', handleInvertedImpulseResponseEvent);

        testIRCalibration.sourceSamplingRate = 96000;
        testIRCalibration.sendRecordingToServerForProcessing(text);
      };

      reader.readAsText(f);
    }
  };

  const handleIIRUplaod = e => {
    const f = e.target.files[0];
    if (f) {
      e.preventDefault();
      const reader = new FileReader();

      reader.onload = async e => {
        const g_string = e.target.result;
        const g = g_string.split('\n').map(val => parseFloat(val));
        console.log({g});
        useIRResult(g);
      };

      reader.readAsText(f);
    }
  };

  previousCaptureCSV.addEventListener('change', handlePreviousCaptureUpload);
  iirCSV.addEventListener('change', handleIIRUplaod);

  flexSwitchCheckIR.onchange = () => {
    flexSwitchCheckVolume.checked = !flexSwitchCheckIR.checked;
  };

  flexSwitchCheckVolume.onchange = () => {
    flexSwitchCheckIR.checked = !flexSwitchCheckVolume.checked;
  };

  document.getElementById('calibrationBeginButton').onclick = async () => {
    let invertedIR;
    const spinner = document.getElementById('spinner');
    const calibrationResult = document.getElementById('calibrationResult');
    const updateTarget = document.getElementById('updates');

    const speakerParameters = {
      siteUrl: window.location.href.substring(0, location.href.lastIndexOf('/')),
      targetElementId: 'display',
    };

    const calibratorParams = {
      numCaptures: document.getElementById('numCapturesInput').value,
      numMLSPerCapture: document.getElementById('numMLSPerCaptureInput').value,
      mlsOrder: document.getElementById('mlsOrder').value,
      download: document.getElementById('flexSwitchCheckDownload').checked,
    };

    const calibrator = new ImpulseResponseCalibration(calibratorParams);

    calibrator.on('update', ({message, ...rest}) => {
      updateTarget.innerHTML = message;
    });

    const runVolumeCalibration = async () => {
      try {
        const dbSPL = await Speaker.startCalibration(
          speakerParameters,
          VolumeCalibration,
          calibratorParams
        );
        calibrationResult.innerText = `Sound Gain ${dbSPL.toFixed(3)} dB SPL`;
        calibrationResult.classList.remove('d-none');
      } catch (err) {
        calibrationResult.innerText = `${err.name}: ${err.message}`;
      }
    };

    const runImpulseResponseCalibration = async () => {
      try {
        invertedIR = await Speaker.startCalibration(speakerParameters, calibrator);
        console.log({invertedIR});
        await useIRResult(invertedIR);
      } catch (err) {
        calibrationResult.innerText = `${err.name}: ${err.message}`;
      }
    };

    if (flexSwitchCheckIR.checked) {
      runImpulseResponseCalibration();
    } else {
      runVolumeCalibration();
    }
  };
};
