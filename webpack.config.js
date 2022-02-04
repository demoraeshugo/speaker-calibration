const webpack = require('webpack')
const path = require('path');

module.exports = {
  mode: 'development',
  entry: './src/main.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].js',
    library: {
      name: 'soundCheck',
      type: 'umd',
    },
  },
  module: {
    rules: [
      { test: /\.css$/, 
        use: [ 'style-loader', 'css-loader', ],
      },
    ],
  },
  // devServer: {
  //   static: {
  //     directory: path.resolve(__dirname, 'dist'),
  //   },
  // },
}
