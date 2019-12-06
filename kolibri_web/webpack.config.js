var path = require('path');
var webpack = require('webpack');

var HtmlWebpackPlugin = require('html-webpack-plugin');
var HtmlWebpackRootPlugin = require('html-webpack-root-plugin');

module.exports = {
    devtool: 'eval',
    mode: 'development',
    entry: {
        app: './src/index.js'
    },
    output: {
        path: path.join(__dirname, '..', 'kolibri_webview_demo', 'static'),
        filename: 'bundle.js',
        publicPath: './'
    },
    plugins: [
        new webpack.HotModuleReplacementPlugin(),
        new HtmlWebpackPlugin(),
        new HtmlWebpackRootPlugin()
    ],
    resolve: {
        extensions: ['.js', '.jsx']
    },
    module: {
        rules: [{
            test: /\.jsx?$/,
            use: ['babel-loader'],
            include: path.join(__dirname, 'src')
        }]
    }
};
