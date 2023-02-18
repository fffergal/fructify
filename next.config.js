module.exports = {
  async rewrites() {
    if (process.env.NODE_ENV === 'production') {
      return []
    }
    return [
      {
        source: '/api/:slug*',
        destination: `http://127.0.0.1:5000/api/:slug*`,
      },
    ]
  }
}
