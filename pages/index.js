import Head from "next/head"

import DefaultStyle from '../default-style'

export default function Index() {
  return (
    <div>
      <Head>
        <title>Fructify</title>
      </Head>
      <div className="horizontal center">
        <div className="vertical">
          <h1>Fructify</h1>
          <p><a href="/api/v1/login">Log in</a></p>
          <p>Make yourself more fruitful.</p>
        </div>
      </div>
      <DefaultStyle/>
    </div>
  )
}
