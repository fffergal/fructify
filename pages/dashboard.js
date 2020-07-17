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

const GoogleLink = () => {
  const {data, error} = useSwr("/api/v1/googlecheck", fetcher)
  if (error) {
    return <p>Error checking Google link</p>
  }
  if (!data) {
    return <p>Checking Google link...</p>
  }
  let action
  if (data.hasGoogle) {
    action = "Change"
  }
  else {
    action = "Link"
  }
  return <p><a href="/api/v1/googlelink">{action} Google account</a></p>
}



const GoogleCalendars = () => {
  const {data, error} = useSwr("/api/v1/googlecalendars", fetcher)
  if (error) {
    return <p>Error getting Google calendars</p>
  }
  if (!data) {
    return <p>Loading Google calendars...</p>
  }
  return (
    <div>
      <p>Google calendars:</p>
      <ul>
        {data.googleCalendars.map(
          ({id, summary}) => <li key={id}>{summary}</li>
        )}
      </ul>
    </div>
  )
}

export default function Dashboard() {
  return (
    <div>
      <Head>
        <title>Fructify Dashboard</title>
      </Head>
      <h1>Fructify Dashboard</h1>
      <LoggedIn>
        <TelegramLink/>
        <TelegramGroups/>
        <GoogleLink/>
        <GoogleCalendars/>
        <p><a href="/api/v1/logout">Log out</a></p>
      </LoggedIn>
      <DefaultStyle/>
    </div>
  )
}
