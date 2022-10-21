const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
        '/predict': {
            target: 'http://192.168.10.220:31018',
            changeOrigin: true
        },

        '/tagging': {
            target: 'http://192.168.10.220:31019',
            changeOrigin: true
        },
        
        '/vector_set/search': {
            target: 'http://192.168.10.220:31018',
            changeOrigin: true
        },

        '/contents': {
            target: 'http://192.168.10.220:31018',
            changeOrigin: true
        }
    }
  }
})
