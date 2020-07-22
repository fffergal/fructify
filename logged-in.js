import PropTypes from "prop-types"
import useSwr from "swr"

import fetcher from "./fetcher"

export default function LoggedIn({children}) {
  const {data, error} = useSwr("/api/v1/authcheck", fetcher)
  if (error) {
    return <p>Could not get logged in status</p>
  }
  if (!data) {
    return <p>Checking if you are logged in...</p>
  }
  if (!data.loggedIn) {
    return <p><a href="/api/v1/login">Log in/Sign up</a></p>
  }
  return (
    <div>
      {children}
    </div>
  )
}
LoggedIn.propTypes = {
  children: PropTypes.element.isRequired
}
