const path = require('path');

module.exports = {
    entry: {
        umt: './public/js/umt.js'
    },
    output: {
        filename: '[name].bundle.js',
        path: path.resolve(__dirname, 'public/dist/js')
    },
    mode: 'production'
};
