import Head from "next/head"
import useSwr from "swr"

import DefaultStyle from "../default-style"
import fetcher from "../fetcher"
import LoggedIn from "../logged-in"


const TelegramLink = () => {
  const {data: deeplinkData, error: deeplinkError} = useSwr(
    "/api/v1/telegramdeeplink", fetcher
  )
  if (deeplinkError) {
    return <p>Error making Telegram deeplink</p>
  }
  if (!deeplinkData) {
    return <p>Loading Telegram deeplink...</p>
  }
  return <p><a href={deeplinkData.deeplinkUrl}>Add Telegram group</a></p>
}

const TelegramGroups = () => {
  const {data, error} = useSwr("/api/v1/telegramchats", fetcher)
  if (error) {
    return <p>Error getting Telegram groups</p>
  }
  if (!data) {
    return <p>Loading Telegram groups...</p>
  }
  return (
    <div>
      <p>Linked Telegram groups:</p>
      <ul>
        {data.telegramGroups.map(
          ({chatTitle, issuerSub}) => <li key={issuerSub}>{chatTitle}</li>
        )}
      </ul>
    </div>
  )
}

export default function Dashboard() {
  return (
    <div className="horizontal center">
      <Head>
        <title>Fructify Dashboard</title>
      </Head>
      <div className="vertical">
        <h1>Fructify Dashboard</h1>
        <LoggedIn>
          <TelegramLink/>
          <p><a href="/api/v1/googlelink">Link Google account</a></p>
          <TelegramGroups/>
          <p><a href="/api/v1/logout">Log out</a></p>
        </LoggedIn>
      </div>
      <DefaultStyle/>
    </div>
  )
}
