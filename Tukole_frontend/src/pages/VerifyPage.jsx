import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'

export default function VerifyPage() {
  const { token } = useParams()
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    async function verifyAccount() {
      try {
        const response = await api.verifyAccount(token)
        setMessage(response.message)
      } catch (requestError) {
        setError(requestError.message)
      } finally {
        setLoading(false)
      }
    }

    verifyAccount()
  }, [token])

  return (
    <section className="page-state page-state--narrow">
      <div className="state-badge">Verification</div>
      <h1>{loading ? 'Verifying your account...' : error ? 'Verification failed' : 'Account ready'}</h1>
      <p>{loading ? 'Please wait while we confirm your account.' : error || message}</p>
      <Link className="button" to="/auth">
        Continue to sign in
      </Link>
    </section>
  )
}
