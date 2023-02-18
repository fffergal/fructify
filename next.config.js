module.exports = {
  async rewrites() {
    if (process.env.NODE_ENV === 'production') {
      return []
    }
    return [
      {
        source: '/api/:slug*',
        destination: `http://localhost:5000/api/:slug*`,
      },
    ]
  }
}
