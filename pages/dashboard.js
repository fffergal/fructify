import Head from "next/head"
import PropTypes from "prop-types"
import React from "react"
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

const TelegramGroups = ({selectId}) => {
  const {data, error} = useSwr("/api/v1/telegramchats", fetcher)
  if (error) {
    return (
      <select><option disabled>Error getting Telegram groups</option></select>
    )
  }
  if (!data) {
    return <select><option disabled>Loading Telegram groups...</option></select>
  }
  return (
    <select id={selectId}>
      {data.telegramGroups.map(
        ({chatTitle, issuerSub}) => (
          <option key={issuerSub} value={issuerSub}>{chatTitle}</option>
        )
      )}
    </select>
  )
}
TelegramGroups.propTypes = {
  selectId: PropTypes.string,
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



const GoogleCalendars = ({selectId}) => {
  const {data, error} = useSwr("/api/v1/googlecalendars", fetcher)
  if (error) {
    return <select><option>Error getting Google calendars</option></select>
  }
  if (!data) {
    return <select><option disabled>Loading Google calendars...</option></select>
  }
  return (
    <select id={selectId}>
      {data.googleCalendars.map(
        ({id, summary}) => <option key={id} value={id}>{summary}</option>
      )}
    </select>
  )
}
GoogleCalendars.propTypes = {
  selectId: PropTypes.string,
}

class NewLink extends React.Component {
  constructor() {
    super()
    this.state = {"buttonText": "Link", "error": false}
  }

  render() {
    const submit = async () => {
      this.setState({"buttonText": "Linking...", "error": false})
      const calendarId = document.getElementById("calendars").value
      const chatId = document.getElementById("chats").value
      try {
        const response = await fetch(
          "/api/v1/googletelegramlinks",
          {
            method: "PUT",
            "headers": {"content-type": "application/json"},
            body: JSON.stringify(
              {"googleCalendarId": calendarId, "telegramChatId": chatId}
            )
          }
        )
        if (!response.ok) {
          this.setState({"error": true})
        }
      } catch {
        this.setState({"error": true})
      }
      this.setState({"buttonText": "Link"})
    }
    let errorP = <p>&nbsp;</p>
    if (this.state.error) {
      errorP = <p>Error linking calendar to chat</p>
    }
    return (
      <div>
        <div>
          <GoogleCalendars selectId="calendars"/>
          <span>&rarr;</span>
          <TelegramGroups selectId="chats"/>
          <button onClick={submit}>{this.state.buttonText}</button>
        </div>
        {errorP}
      </div>
    )
  }
}

const GoogleTelegramLinks = () => {
  const {data, error} = useSwr("/api/v1/googletelegramlinks", fetcher)
  if (error) {
    return <p>Error loading Google calendar/Telegram group links</p>
  }
  if (!data) {
    return <p>Loading Google calendar/Telegram group links...</p>
  }
  return (
    <ul>
      {data.googleTelegramLinks.map(
        ({
          googleCalenderId,
          googleCalendarSummary,
          telegramChatId,
          telegramChatTitle,
        }) => (
          <li key={googleCalenderId + "-" + telegramChatId}>
            {googleCalendarSummary} &rarr; {telegramChatTitle}
          </li>
        )
      )}
    </ul>
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
        <div>
          <TelegramLink/>
          <GoogleLink/>
          <p>Link Google calendar to Telegram group:</p>
          <NewLink/>
          <p>Google calendar/Telegram group links:</p>
          <GoogleTelegramLinks/>
          <p><a href="/api/v1/logout">Log out</a></p>
        </div>
      </LoggedIn>
      <DefaultStyle/>
    </div>
  )
}
