// eslint-disable-next-line import/extensions
const createMLSGenModule = require('../../dist/mlsGen.js');

/**
 * MLSGenInterface provides a class for interfacing with the MLSGen WASM module.
 */
class MlsGenInterface {
  /** @private */
  #N = 18;

  /** @private */
  // eslint-disable-next-line no-bitwise
  #P = (1 << 18) - 1; 

  /** @private */
  #MLSGen;

  /** @private */
  #WASMInstance;

  /**
   * Creates an instance of MlsGenInterface.
   * Makes a call to the WASM glue code to load the WASM module.
   */
  constructor() {
    // load the WASM module and save the instance.
    createMLSGenModule().then((instance) => {
      this.#WASMInstance = instance;
      this.#MLSGen = new instance.MLSGen(this.N);
      console.log(this.#MLSGen);
    });
  }

  /* 
  TODO: Figure out the best way to interact with this module.
        1. Return the MLS signal (as an array), appears problematic with the pointer bindings
        2. Pass a buffer to the function to be filled with the MLS, I did this before but need
           to go back and look at how it was done. Currently throwing an error.
        3. Circumvent this all together by calling the webAudio API in the CPP code directly.
  */
  getMls = () => {
  /**
   * Calculate the Maximum Length Sequence (MLS) with period P = 2^N - 1 
   * using the MLSGen WASM module.
   * @param {Number} N 
   */
    // Get function.
    const { HEAPU8 } = this.#WASMInstance;

    // Create the arrays.
    // eslint-disable-next-line no-bitwise
    const offset = 0;
    const result = new Uint8Array(HEAPU8.buffer, offset, this.#P);

    // Call the function.
    this.#MLSGen.getMls(result.byteOffset, this.#N, this.#P);

    console.log(result);
  }
}

export default MlsGenInterface;
