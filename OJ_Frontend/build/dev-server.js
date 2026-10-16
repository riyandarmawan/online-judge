'use strict'
require('./check-versions')()

const config = require('../config')
if (!process.env.NODE_ENV) {
  process.env.NODE_ENV = JSON.parse(config.dev.env.NODE_ENV)
}

const opn = require('opn')
const path = require('path')
const express = require('express')
const webpack = require('webpack')
const proxyMiddleware = require('http-proxy-middleware')
const webpackConfig = require('./webpack.dev.conf')

// default port where dev server listens for incoming traffic
const port = process.env.PORT || config.dev.port
// automatically open browser, if not set will be false
const autoOpenBrowser = !!config.dev.autoOpenBrowser
// Define HTTP proxies to your custom API backend
// https://github.com/chimurai/http-proxy-middleware
const proxyTable = config.dev.proxyTable

const app = express()

function isPrivateAddress (raw) {
  if (!raw) return false
  let ip = raw
  if (ip.startsWith('::ffff:')) ip = ip.slice(7)
  if (ip === '::1' || ip === '127.0.0.1') return true
  if (ip.startsWith('10.') || ip.startsWith('192.168.')) return true
  const linkLocal = ip.startsWith('fe80:') || ip.startsWith('fc') || ip.startsWith('fd')
  if (linkLocal) return true
  if (ip.startsWith('172.')) {
    const second = parseInt(ip.split('.')[1], 10)
    return second >= 16 && second <= 31
  }
  return false
}

function readCookie (header, name) {
  return (header || '').split(';').reduce((found, part) => {
    const pieces = part.trim().split('=')
    if (pieces[0] === name) return decodeURIComponent(pieces.slice(1).join('='))
    return found
  }, '')
}

function portalSecret () {
  const fs = require('fs')
  const crypto = require('crypto')
  const keyPath = path.resolve(__dirname, '../../Deploy/data/backend/config/dosen_portal.key')
  fs.mkdirSync(path.dirname(keyPath), {recursive: true})
  if (!fs.existsSync(keyPath)) {
    fs.writeFileSync(keyPath, crypto.randomBytes(24).toString('hex'))
  }
  return fs.readFileSync(keyPath, 'utf8').trim()
}

const dosenPortalSecret = portalSecret()

app.use((req, res, next) => {
  if (!isPrivateAddress(req.socket.remoteAddress || req.connection.remoteAddress)) {
    res.status(403).type('text').send('Aplikasi hanya dapat diakses dari jaringan lokal.')
    return
  }
  const urlPath = req.path
  if (urlPath === '/' + dosenPortalSecret) {
    res.cookie('dosen_portal', dosenPortalSecret, {httpOnly: true, sameSite: 'lax', path: '/'})
    res.redirect(302, '/' + dosenPortalSecret + '/')
    return
  }
  if (urlPath === '/' + dosenPortalSecret + '/' || urlPath.startsWith('/' + dosenPortalSecret + '/')) {
    res.cookie('dosen_portal', dosenPortalSecret, {httpOnly: true, sameSite: 'lax', path: '/'})
    req.url = '/admin/index.html'
    next()
    return
  }
  if (/^\/admin(\/|$|\.)/.test(urlPath)) {
    if (readCookie(req.headers.cookie, 'dosen_portal') !== dosenPortalSecret) {
      res.status(404).type('text').send('Not Found')
      return
    }
  }
  next()
})

const compiler = webpack(webpackConfig)

const devMiddleware = require('webpack-dev-middleware')(compiler, {
  publicPath: webpackConfig.output.publicPath,
  quiet: true
})

const hotMiddleware = require('webpack-hot-middleware')(compiler, {
  log: false,
  heartbeat: 2000
})
// force page reload when html-webpack-plugin template changes
// currently disabled until this is resolved:
// https://github.com/jantimon/html-webpack-plugin/issues/680
// compiler.plugin('compilation', function (compilation) {
//   compilation.plugin('html-webpack-plugin-after-emit', function (data, cb) {
//     hotMiddleware.publish({ action: 'reload' })
//     cb()
//   })
// })

// enable hot-reload and state-preserving
// compilation error display
app.use(hotMiddleware)

// proxy api requests
Object.keys(proxyTable).forEach(function (context) {
  let options = proxyTable[context]
  if (typeof options === 'string') {
    options = { target: options }
  }
  app.use(proxyMiddleware(options.filter || context, options))
})

// handle fallback for HTML5 history API
const rewrites = {
  rewrites: [{
    from: '/admin/', // 正则或者字符串
    to: '/admin/index.html', // 字符串或者函数
  }]
}
const historyMiddleware = require('connect-history-api-fallback')(rewrites);
app.use(historyMiddleware)

// serve webpack bundle output
app.use(devMiddleware)

// serve pure static assets
const staticPath = path.posix.join(config.dev.assetsPublicPath, config.dev.assetsSubDirectory)
app.use(staticPath, express.static('./static'))

const uri = 'http://localhost:' + port

var _resolve
var _reject
var readyPromise = new Promise((resolve, reject) => {
  _resolve = resolve
  _reject = reject
})

var server
var portfinder = require('portfinder')
portfinder.basePort = port

console.log('> Starting dev server...')
devMiddleware.waitUntilValid(() => {
  portfinder.getPort((err, port) => {
    if (err) {
      _reject(err)
    }
    process.env.PORT = port
    var uri = 'http://localhost:' + port
    console.log('> Listening at ' + uri + '\n')
    console.log('> Portal dosen (simpan, jangan dibagikan ke mahasiswa):')
    console.log('>   http://localhost:' + port + '/' + dosenPortalSecret + '/')
    // when env is testing, don't need open it
    if (autoOpenBrowser && process.env.NODE_ENV !== 'testing') {
      opn(uri)
    }
    server = app.listen(port)
    _resolve()
  })
})

module.exports = {
  ready: readyPromise,
  close: () => {
    server.close()
  }
}
