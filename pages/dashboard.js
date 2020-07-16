import Head from "next/head"
import useSwr from "swr"

import DefaultStyle from "../default-style"

const fetcher = (...args) => fetch(...args).then(res => res.json())

const TelegramLink = () => {
  const {data: deeplinkData, error: deeplinkError} = useSwr(
    "/api/v1/telegramdeeplink", fetcher
  )
  if (deeplinkError) {
    return <p>Error making Telegram deeplink</p>
  }
  else if (!deeplinkData) {
    return <p>Loading Telegram deeplink...</p>
  }
  else {
    return <p><a href={deeplinkData.deeplinkUrl}>Add Telegram group</a></p>
  }
}

export default function Dashboard() {
  return (
    <div className="horizontal center">
      <Head>
        <title>Fructify Dashboard</title>
      </Head>
      <div className="vertical">
        <h1>Fructify Dashboard</h1>
        <TelegramLink/>
        <p><a href="/api/v1/googlelink">Link Google account</a></p>
      </div>
      <DefaultStyle/>
    </div>
  )
}
