import Head from "next/head"
import Link from "next/link"

import DefaultStyle from "../default-style"
import LoggedIn from "../logged-in"

export default function Index() {
  return (
    <div>
      <Head>
        <title>Fructify</title>
      </Head>
      <h1>Fructify</h1>
      <LoggedIn>
        <p><Link href="/dashboard">Go to dashboard</Link></p>
      </LoggedIn>
      <p>Make yourself more fruitful.</p>
      <DefaultStyle/>
    </div>
  )
}
