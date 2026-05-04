import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { SectionTitle } from '../components/SectionTitle'
import { StatCard } from '../components/StatCard'
import { StatusPill, formatStatusLabel } from '../components/StatusPill'
import { useAuth } from '../context/AuthContext'

function formatCurrency(value) {
  return new Intl.NumberFormat('en-UG', {
    style: 'currency',
    currency: 'UGX',
    maximumFractionDigits: 0,
  }).format(Number(value || 0))
}

function formatDateTime(value) {
  if (!value) {
    return 'Not scheduled'
  }

  return new Intl.DateTimeFormat('en-UG', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

const initialWorkspace = {
  adminDashboard: null,
  adminDisputes: [],
  adminProviders: [],
  adminUsers: [],
  analytics: null,
  bookings: [],
  deletedBookings: [],
  deletedReviews: [],
  notifications: [],
  payments: [],
  providerBookings: [],
  providerProfile: null,
  providerServices: [],
  providers: [],
  reviews: [],
  services: [],
  unreadCount: 0,
}

export default function DashboardPage() {
  const { authReady, authorizedRequest, isAuthenticated, user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [workspace, setWorkspace] = useState(initialWorkspace)
  const [bookingForm, setBookingForm] = useState({ bookingDate: '', serviceId: '' })
  const [paymentForm, setPaymentForm] = useState({ amount: '', bookingId: '' })
  const [reviewForm, setReviewForm] = useState({ bookingId: '', comment: '', rating: 5 })
  const [disputeForm, setDisputeForm] = useState({ bookingId: '', description: '', reason: '' })
  const [providerForm, setProviderForm] = useState({ bio: '', business_name: '' })
  const [serviceForm, setServiceForm] = useState({ description: '', name: '', price: '' })
  const [adminRoleDrafts, setAdminRoleDrafts] = useState({})
  const [disputeResponses, setDisputeResponses] = useState({})
  const [serviceSearch, setServiceSearch] = useState('')
  const [editingService, setEditingService] = useState(null)
  const [editServiceForm, setEditServiceForm] = useState({ description: '', name: '', price: '' })

  const providerMode = user?.role === 'provider' || user?.role === 'admin'
  const adminMode = user?.role === 'admin'
  const serviceLookup = Object.fromEntries(workspace.services.map((service) => [service.uid, service]))
  const myReviews = workspace.reviews.filter((review) => review.reviewer_id === user?.uid)
  const filteredServices = workspace.services.filter((s) =>
    s.name.toLowerCase().includes(serviceSearch.toLowerCase()),
  )

  function serviceNameForReview(bookingId) {
    const booking = workspace.bookings.find((b) => b.uid === bookingId)
    return booking ? serviceLookup[booking.service_id]?.name || 'Unknown service' : 'Unknown booking'
  }

  async function loadWorkspaceData(showLoader = true) {
    if (showLoader) {
      setLoading(true)
    }

    try {
      const [
        services,
        providers,
        reviews,
        bookings,
        notifications,
        unreadNotifications,
        providerBookings,
        providerProfile,
        adminDashboard,
        adminUsers,
        adminDisputes,
        deletedBookings,
        deletedReviews,
        adminProviders,
      ] = await Promise.all([
        api.getServices(),
        api.getProviders(),
        api.getReviews(),
        authorizedRequest((token) => api.getMyBookings(token)),
        authorizedRequest((token) => api.getNotifications(token)),
        authorizedRequest((token) => api.getUnreadNotifications(token)),
        providerMode
          ? authorizedRequest((token) => api.getProviderBookings(token)).catch((error) =>
              error.status === 404 ? [] : Promise.reject(error),
            )
          : Promise.resolve([]),
        providerMode
          ? authorizedRequest((token) => api.getMyProvider(user.uid, token)).catch((error) =>
              error.status === 404 ? null : Promise.reject(error),
            )
          : Promise.resolve(null),
        adminMode ? authorizedRequest((token) => api.getAdminDashboard(token)) : Promise.resolve(null),
        adminMode ? authorizedRequest((token) => api.getAdminUsers(token)) : Promise.resolve([]),
        adminMode ? authorizedRequest((token) => api.getAdminDisputes(token)) : Promise.resolve([]),
        adminMode ? authorizedRequest((token) => api.getDeletedBookings(token)) : Promise.resolve([]),
        adminMode ? authorizedRequest((token) => api.getDeletedReviews(token)) : Promise.resolve([]),
        adminMode ? authorizedRequest((token) => api.getAdminProviders(token)) : Promise.resolve([]),
      ])

      let providerServices = []
      if (providerProfile?.uid) {
        try {
          providerServices = await api.getProviderServices(providerProfile.uid)
        } catch {
          providerServices = []
        }
      }

      setWorkspace((current) => ({
        ...current,
        adminDashboard,
        adminDisputes,
        adminProviders,
        adminUsers,
        analytics: adminDashboard,
        bookings,
        deletedBookings,
        deletedReviews,
        notifications,
        providerBookings,
        providerProfile,
        providerServices,
        providers,
        reviews,
        services,
        unreadCount: unreadNotifications.length,
      }))

      setProviderForm({
        bio: providerProfile?.bio || '',
        business_name: providerProfile?.business_name || '',
      })

      setAdminRoleDrafts((current) => {
        const next = { ...current }
        adminUsers.forEach((adminUser) => {
          if (!next[adminUser.uid]) {
            next[adminUser.uid] = adminUser.role
          }
        })
        return next
      })

      setDisputeResponses((current) => {
        const next = { ...current }
        adminDisputes.forEach((dispute) => {
          if (next[dispute.uid] === undefined) {
            next[dispute.uid] = dispute.admin_response || ''
          }
        })
        return next
      })
    } catch (error) {
      setFeedback({ tone: 'error', message: error.message })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (authReady && isAuthenticated) {
      loadWorkspaceData()
    }
  }, [authReady, isAuthenticated, user?.role])

  useEffect(() => {
    if (!feedback) return
    const timer = setTimeout(() => setFeedback(null), 5000)
    return () => clearTimeout(timer)
  }, [feedback])

  async function runAction(label, action, options = {}) {
    const { reload = true, successMessage = label } = options
    setBusy(label)
    setFeedback(null)

    try {
      const result = await action()
      if (reload) {
        await loadWorkspaceData(false)
      }
      setFeedback({ tone: 'success', message: successMessage })
      return result
    } catch (error) {
      setFeedback({ tone: 'error', message: error.message })
      return null
    } finally {
      setBusy('')
    }
  }

  async function handleCreateBooking(event) {
    event.preventDefault()
    await runAction(
      'Creating booking',
      () =>
        authorizedRequest((token) =>
          api.createBooking(
            {
              booking_date: bookingForm.bookingDate,
              service_id: bookingForm.serviceId,
            },
            token,
          ),
        ),
      { successMessage: 'Booking created successfully.' },
    )
    setBookingForm({ bookingDate: '', serviceId: '' })
  }

  async function handleCreatePayment(event) {
    event.preventDefault()
    const payment = await runAction(
      'Creating payment',
      () =>
        authorizedRequest((token) =>
          api.createPayment(
            { amount: Number(paymentForm.amount), booking_id: paymentForm.bookingId },
            token,
          ),
        ),
      { reload: false, successMessage: 'Payment created in pending state.' },
    )

    if (payment) {
      setWorkspace((current) => ({ ...current, payments: [payment, ...current.payments] }))
      setPaymentForm({ amount: '', bookingId: '' })
    }
  }

  async function handleCreateReview(event) {
    event.preventDefault()
    await runAction(
      'Creating review',
      () =>
        authorizedRequest((token) =>
          api.createReview(
            {
              booking_id: reviewForm.bookingId,
              comment: reviewForm.comment,
              rating: Number(reviewForm.rating),
            },
            token,
          ),
        ),
      { successMessage: 'Review published.' },
    )
    setReviewForm({ bookingId: '', comment: '', rating: 5 })
  }

  async function handleCreateDispute(event) {
    event.preventDefault()
    await runAction(
      'Opening dispute',
      () =>
        authorizedRequest((token) =>
          api.createDispute(
            {
              booking_id: disputeForm.bookingId,
              description: disputeForm.description,
              reason: disputeForm.reason,
            },
            token,
          ),
        ),
      { reload: false, successMessage: 'Dispute submitted.' },
    )
    setDisputeForm({ bookingId: '', description: '', reason: '' })
  }

  async function handleCancelBooking(bookingId) {
    if (!window.confirm('Cancel this booking?')) {
      return
    }

    await runAction(
      'Cancelling booking',
      () => authorizedRequest((token) => api.cancelBooking(bookingId, token, 'Cancelled from workspace')),
      { successMessage: 'Booking cancelled.' },
    )
  }

  async function handleDeleteService(serviceId) {
    if (!window.confirm('Delete this service? This cannot be undone.')) return
    await runAction(
      'Deleting service',
      () => authorizedRequest((token) => api.deleteService(serviceId, token)),
      { successMessage: 'Service deleted.' },
    )
    setEditingService(null)
  }

  async function handleUpdateService(event) {
    event.preventDefault()
    if (!editingService) return
    await runAction(
      'Updating service',
      () =>
        authorizedRequest((token) =>
          api.updateService(
            editingService.uid,
            {
              description: editServiceForm.description,
              name: editServiceForm.name,
              price: Number(editServiceForm.price),
            },
            token,
          ),
        ),
      { successMessage: 'Service updated.' },
    )
    setEditingService(null)
  }

  if (!authReady || !isAuthenticated) {
    return null
  }

  if (loading) {
    return (
      <section className="page-state">
        <div className="state-badge">Loading</div>
        <h1>Building your workspace...</h1>
        <p>We are gathering your services, bookings, and notifications.</p>
      </section>
    )
  }

  return (
    <div className="page-stack">
      <section className="hero-panel hero-panel--workspace">
        <div className="hero-panel__copy">
          <p className="eyebrow">Workspace</p>
          <h1>Welcome back, {user.first_name || user.username}.</h1>
          <p className="hero-panel__text">Manage bookings, payments, reviews, disputes, and alerts from one place.</p>
          <div className="hero-panel__actions">
            <button className="button" onClick={() => loadWorkspaceData(false)} type="button">Refresh data</button>
            <Link className="button button--ghost" to="/">Visit landing page</Link>
          </div>
        </div>
        <div className="hero-panel__spotlight">
          <div className="workspace-profile">
            <StatusPill status={user.role} />
            <h2>{user.username}</h2>
            <p>{user.email}</p>
            <div className="workspace-profile__meta">
              <span>{user.is_active ? 'Verified account' : 'Pending verification'}</span>
              <span>{providerMode ? 'Provider tools enabled' : 'Customer workspace'}</span>
              <span>{adminMode ? 'Admin controls enabled' : 'Standard access'}</span>
            </div>
          </div>
        </div>
      </section>
      {feedback ? <div className={`feedback feedback--${feedback.tone}`}>{feedback.message}</div> : null}

      <div className="stat-grid">
        <StatCard accent="sun" detail="Marketplace services" label="Services" value={workspace.services.length} />
        <StatCard accent="sea" detail="Your bookings" label="My bookings" value={workspace.bookings.length} />
        <StatCard accent="leaf" detail="Unread alerts" label="Notifications" value={workspace.unreadCount} />
        <StatCard accent="violet" detail={adminMode ? 'Released revenue' : 'Reviews you wrote'} label={adminMode ? 'Revenue' : 'My reviews'} value={adminMode ? formatCurrency(workspace.adminDashboard?.released_revenue || 0) : myReviews.length} />
      </div>

      <div className="workspace-grid">
        <section className="panel panel--span-2">
          <SectionTitle eyebrow="Marketplace" title="Available services" description="Pick a service and start a booking." />
          <label className="field" style={{ marginBottom: '0.5rem' }}>
            <input
              onChange={(event) => setServiceSearch(event.target.value)}
              placeholder="Search services by name..."
              type="search"
              value={serviceSearch}
            />
          </label>
          <div className="card-grid">
            {filteredServices.length ? (
              filteredServices.map((service) => (
                <article className="service-card" key={service.uid}>
                  <div className="service-card__top">
                    <StatusPill status="accepted" />
                    <span className="service-card__price">{formatCurrency(service.price)}</span>
                  </div>
                  <h3>{service.name}</h3>
                  <p>{service.description || 'No description available yet.'}</p>
                  <button className="button button--ghost button--small" onClick={() => setBookingForm((current) => ({ ...current, serviceId: service.uid }))} type="button">Select</button>
                </article>
              ))
            ) : (
              <div className="empty-state">
                <p>{serviceSearch ? `No services match "${serviceSearch}".` : 'No services have been published yet.'}</p>
              </div>
            )}
          </div>
        </section>

        <aside className="panel">
          <SectionTitle eyebrow="Action" title="Create booking" description="Posts to `/bookings/`." />
          <form className="form-stack" onSubmit={handleCreateBooking}>
            <label className="field">
              <span>Service</span>
              <select onChange={(event) => setBookingForm((current) => ({ ...current, serviceId: event.target.value }))} required value={bookingForm.serviceId}>
                <option value="">Choose service</option>
                {workspace.services.map((service) => (
                  <option key={service.uid} value={service.uid}>
                    {service.name} · {formatCurrency(service.price)}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Date</span>
              <input min={new Date().toISOString().slice(0, 16)} onChange={(event) => setBookingForm((current) => ({ ...current, bookingDate: event.target.value }))} required type="datetime-local" value={bookingForm.bookingDate} />
            </label>
            <button className="button button--block" disabled={Boolean(busy)} type="submit">
              {busy === 'Creating booking' ? 'Creating...' : 'Create booking'}
            </button>
          </form>
        </aside>
      </div>

      <div className="workspace-grid">
        <section className="panel panel--span-2">
          <SectionTitle eyebrow="Bookings" title="My booking history" description="Pay, review, dispute, or cancel from here." />
          <div className="stack-list">
            {workspace.bookings.length ? (
              workspace.bookings.map((booking) => {
                const service = serviceLookup[booking.service_id]

                return (
                  <article className="list-card" key={booking.uid}>
                    <div className="list-card__main">
                      <div className="list-card__title-row">
                        <h3>{service?.name || 'Booked service'}</h3>
                        <StatusPill status={booking.status} />
                      </div>
                      <p>{formatDateTime(booking.booking_date)}</p>
                      <small>{service ? formatCurrency(service.price) : 'Price unavailable'}</small>
                    </div>
                    <div className="list-card__actions">
                      <button className="button button--ghost button--small" onClick={() => setPaymentForm({ amount: service?.price ? String(service.price) : '', bookingId: booking.uid })} type="button">Pay</button>
                      <button className="button button--ghost button--small" onClick={() => setReviewForm((current) => ({ ...current, bookingId: booking.uid }))} type="button">Review</button>
                      <button className="button button--ghost button--small" onClick={() => setDisputeForm((current) => ({ ...current, bookingId: booking.uid }))} type="button">Dispute</button>
                      {booking.status !== 'completed' && booking.status !== 'cancelled' ? (
                        <button className="button button--danger button--small" onClick={() => handleCancelBooking(booking.uid)} type="button">Cancel</button>
                      ) : null}
                    </div>
                  </article>
                )
              })
            ) : (
              <div className="empty-state"><p>No bookings yet.</p></div>
            )}
          </div>
        </section>

        <aside className="stack-panel">
          <section className="panel">
            <SectionTitle eyebrow="Payments" title="Create payment" description="The amount should match the service price." />
            <form className="form-stack" onSubmit={handleCreatePayment}>
              <label className="field">
                <span>Booking</span>
                <select
                  onChange={(event) => {
                    const booking = workspace.bookings.find((item) => item.uid === event.target.value)
                    const service = booking ? serviceLookup[booking.service_id] : null
                    setPaymentForm({ amount: service?.price ? String(service.price) : '', bookingId: event.target.value })
                  }}
                  required
                  value={paymentForm.bookingId}
                >
                  <option value="">Choose booking</option>
                  {workspace.bookings.map((booking) => (
                    <option key={booking.uid} value={booking.uid}>
                      {serviceLookup[booking.service_id]?.name || booking.uid}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Amount</span>
                <input onChange={(event) => setPaymentForm((current) => ({ ...current, amount: event.target.value }))} required step="0.01" type="number" value={paymentForm.amount} />
              </label>
              <button className="button button--block" disabled={Boolean(busy)} type="submit">
                {busy === 'Creating payment' ? 'Saving...' : 'Create payment'}
              </button>
            </form>
            {workspace.payments.length ? (
              <div className="mini-list">
                {workspace.payments.map((payment) => (
                  <article className="mini-list__item" key={payment.uid}>
                    <div>
                      <strong>{formatCurrency(payment.amount)}</strong>
                      <p>{payment.uid}</p>
                    </div>
                    <StatusPill status={payment.status} />
                  </article>
                ))}
              </div>
            ) : null}
          </section>

          <section className="panel">
            <SectionTitle eyebrow="Reviews" title="Leave feedback" description="Create a review for one of your bookings." />
            <form className="form-stack" onSubmit={handleCreateReview}>
              <label className="field">
                <span>Booking</span>
                <select onChange={(event) => setReviewForm((current) => ({ ...current, bookingId: event.target.value }))} required value={reviewForm.bookingId}>
                  <option value="">Choose booking</option>
                  {workspace.bookings.map((booking) => (
                    <option key={booking.uid} value={booking.uid}>
                      {serviceLookup[booking.service_id]?.name || booking.uid}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Rating</span>
                <select onChange={(event) => setReviewForm((current) => ({ ...current, rating: event.target.value }))} value={reviewForm.rating}>
                  <option value="5">5</option>
                  <option value="4">4</option>
                  <option value="3">3</option>
                  <option value="2">2</option>
                  <option value="1">1</option>
                </select>
              </label>
              <label className="field">
                <span>Comment</span>
                <textarea onChange={(event) => setReviewForm((current) => ({ ...current, comment: event.target.value }))} rows="3" value={reviewForm.comment} />
              </label>
              <button className="button button--block" disabled={Boolean(busy)} type="submit">
                {busy === 'Creating review' ? 'Publishing...' : 'Publish review'}
              </button>
            </form>
          </section>

          <section className="panel">
            <SectionTitle eyebrow="Disputes" title="Open dispute" description="Send a dispute to the admin queue." />
            <form className="form-stack" onSubmit={handleCreateDispute}>
              <label className="field">
                <span>Booking</span>
                <select onChange={(event) => setDisputeForm((current) => ({ ...current, bookingId: event.target.value }))} required value={disputeForm.bookingId}>
                  <option value="">Choose booking</option>
                  {workspace.bookings.map((booking) => (
                    <option key={booking.uid} value={booking.uid}>
                      {serviceLookup[booking.service_id]?.name || booking.uid}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Reason</span>
                <input onChange={(event) => setDisputeForm((current) => ({ ...current, reason: event.target.value }))} required type="text" value={disputeForm.reason} />
              </label>
              <label className="field">
                <span>Description</span>
                <textarea onChange={(event) => setDisputeForm((current) => ({ ...current, description: event.target.value }))} rows="3" value={disputeForm.description} />
              </label>
              <button className="button button--block" disabled={Boolean(busy)} type="submit">
                {busy === 'Opening dispute' ? 'Opening...' : 'Open dispute'}
              </button>
            </form>
          </section>
        </aside>
      </div>

      <div className="workspace-grid">
        <section className="panel panel--span-2">
          <SectionTitle
            eyebrow="Notifications"
            title="Recent updates"
            description="Recent alerts from bookings and marketplace events."
            action={<button className="button button--ghost" onClick={() => runAction('Marking notifications', () => authorizedRequest((token) => api.markAllNotificationsRead(token)), { successMessage: 'All notifications marked as read.' })} type="button">Mark all read</button>}
          />
          <div className="stack-list">
            {workspace.notifications.length ? (
              workspace.notifications.map((notification) => (
                <article className="list-card" key={notification.uid}>
                  <div className="list-card__main">
                    <div className="list-card__title-row">
                      <h3>{formatStatusLabel(notification.notification_type)}</h3>
                      <StatusPill status={notification.is_read ? 'accepted' : 'unread'} />
                    </div>
                    <p>{notification.message}</p>
                    <small>{formatDateTime(notification.created_at)}</small>
                  </div>
                  {!notification.is_read ? (
                    <button className="button button--ghost button--small" onClick={() => runAction('Marking notification', () => authorizedRequest((token) => api.markNotificationRead(notification.uid, token)), { successMessage: 'Notification marked as read.' })} type="button">Read</button>
                  ) : null}
                </article>
              ))
            ) : (
              <div className="empty-state"><p>No notifications yet.</p></div>
            )}
          </div>
        </section>

        <aside className="panel">
          <SectionTitle eyebrow="Reputation" title="My reviews" description="Reviews you already published." />
          <div className="mini-list">
            {myReviews.length ? (
              myReviews.map((review) => (
                <article className="mini-list__item" key={review.uid}>
                  <div>
                    <strong>{review.rating}/5 · {serviceNameForReview(review.booking_id)}</strong>
                    <p>{review.comment || 'No comment provided.'}</p>
                  </div>
                  <StatusPill status="completed" />
                </article>
              ))
            ) : (
              <div className="empty-state empty-state--compact"><p>No reviews yet.</p></div>
            )}
          </div>
        </aside>
      </div>

      {providerMode ? (
        <div className="workspace-grid">
          <section className="panel">
            <SectionTitle eyebrow="Provider studio" title="Provider profile" description="Shape how customers see your business." />
            <form
              className="form-stack"
              onSubmit={async (event) => {
                event.preventDefault()
                await runAction(
                  'Saving provider profile',
                  () =>
                    authorizedRequest((token) =>
                      workspace.providerProfile
                        ? api.updateProvider(workspace.providerProfile.user_id, providerForm, token)
                        : api.createProvider(providerForm, token),
                    ),
                  {
                    successMessage: workspace.providerProfile
                      ? 'Provider profile updated.'
                      : 'Provider profile created.',
                  },
                )
              }}
            >
              <label className="field">
                <span>Business name</span>
                <input onChange={(event) => setProviderForm((current) => ({ ...current, business_name: event.target.value }))} required type="text" value={providerForm.business_name} />
              </label>
              <label className="field">
                <span>Bio</span>
                <textarea onChange={(event) => setProviderForm((current) => ({ ...current, bio: event.target.value }))} rows="4" value={providerForm.bio} />
              </label>
              <button className="button button--block" disabled={Boolean(busy)} type="submit">
                {busy === 'Saving provider profile' ? 'Saving...' : 'Save profile'}
              </button>
            </form>
          </section>

          <section className="panel">
            <SectionTitle eyebrow="Provider studio" title="Publish service" description="Creates a new service on the marketplace." />
            <form
              className="form-stack"
              onSubmit={async (event) => {
                event.preventDefault()
                await runAction(
                  'Publishing service',
                  () =>
                    authorizedRequest((token) =>
                      api.createService(
                        {
                          description: serviceForm.description,
                          name: serviceForm.name,
                          price: Number(serviceForm.price),
                        },
                        token,
                      ),
                    ),
                  { successMessage: 'Service published.' },
                )
                setServiceForm({ description: '', name: '', price: '' })
              }}
            >
              <label className="field">
                <span>Name</span>
                <input onChange={(event) => setServiceForm((current) => ({ ...current, name: event.target.value }))} required type="text" value={serviceForm.name} />
              </label>
              <label className="field">
                <span>Description</span>
                <textarea onChange={(event) => setServiceForm((current) => ({ ...current, description: event.target.value }))} rows="4" value={serviceForm.description} />
              </label>
              <label className="field">
                <span>Price</span>
                <input onChange={(event) => setServiceForm((current) => ({ ...current, price: event.target.value }))} required step="0.01" type="number" value={serviceForm.price} />
              </label>
              <button className="button button--block" disabled={Boolean(busy)} type="submit">
                {busy === 'Publishing service' ? 'Publishing...' : 'Publish service'}
              </button>
            </form>
          </section>

          <section className="panel panel--span-3">
            <SectionTitle eyebrow="Provider studio" title="Provider bookings" description="Complete or cancel work tied to your services." />
            <div className="stack-list">
              {workspace.providerBookings.length ? (
                workspace.providerBookings.map((booking) => (
                  <article className="list-card" key={booking.uid}>
                    <div className="list-card__main">
                      <div className="list-card__title-row">
                        <h3>{serviceLookup[booking.service_id]?.name || booking.uid}</h3>
                        <StatusPill status={booking.status} />
                      </div>
                      <p>{formatDateTime(booking.booking_date)}</p>
                      <small>{booking.customer_id}</small>
                    </div>
                    <div className="list-card__actions">
                      {booking.status !== 'completed' ? (
                        <button className="button button--ghost button--small" onClick={() => runAction('Updating booking', () => authorizedRequest((token) => api.updateBookingStatus(booking.uid, 'completed', token)), { successMessage: 'Booking marked completed.' })} type="button">Complete</button>
                      ) : null}
                      {booking.status !== 'cancelled' ? (
                        <button className="button button--danger button--small" onClick={() => runAction('Updating booking', () => authorizedRequest((token) => api.updateBookingStatus(booking.uid, 'cancelled', token)), { successMessage: 'Booking cancelled.' })} type="button">Cancel</button>
                      ) : null}
                    </div>
                  </article>
                ))
              ) : (
                <div className="empty-state"><p>No provider bookings yet.</p></div>
              )}
            </div>
          </section>

          <section className="panel panel--span-3">
            <SectionTitle
              eyebrow="Provider studio"
              title="My published services"
              description={editingService ? `Editing: ${editingService.name}` : 'Edit or remove services you have published.'}
              action={
                editingService ? (
                  <button className="button button--ghost" onClick={() => setEditingService(null)} type="button">
                    Cancel edit
                  </button>
                ) : null
              }
            />
            {editingService ? (
              <form className="form-stack" onSubmit={handleUpdateService}>
                <label className="field">
                  <span>Name</span>
                  <input
                    onChange={(event) => setEditServiceForm((current) => ({ ...current, name: event.target.value }))}
                    required
                    type="text"
                    value={editServiceForm.name}
                  />
                </label>
                <label className="field">
                  <span>Description</span>
                  <textarea
                    onChange={(event) => setEditServiceForm((current) => ({ ...current, description: event.target.value }))}
                    rows="3"
                    value={editServiceForm.description}
                  />
                </label>
                <label className="field">
                  <span>Price (UGX)</span>
                  <input
                    onChange={(event) => setEditServiceForm((current) => ({ ...current, price: event.target.value }))}
                    required
                    step="0.01"
                    type="number"
                    value={editServiceForm.price}
                  />
                </label>
                <div className="service-edit-actions">
                  <button className="button" disabled={Boolean(busy)} type="submit">
                    {busy === 'Updating service' ? 'Saving...' : 'Save changes'}
                  </button>
                  <button
                    className="button button--danger"
                    disabled={Boolean(busy)}
                    onClick={() => handleDeleteService(editingService.uid)}
                    type="button"
                  >
                    {busy === 'Deleting service' ? 'Deleting...' : 'Delete service'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="card-grid">
                {workspace.providerServices.length ? (
                  workspace.providerServices.map((service) => (
                    <article className="service-card" key={service.uid}>
                      <div className="service-card__top">
                        <StatusPill status="accepted" />
                        <span className="service-card__price">{formatCurrency(service.price)}</span>
                      </div>
                      <h3>{service.name}</h3>
                      <p>{service.description || 'No description provided.'}</p>
                      <button
                        className="button button--ghost button--small"
                        onClick={() => {
                          setEditingService(service)
                          setEditServiceForm({
                            description: service.description || '',
                            name: service.name,
                            price: String(service.price),
                          })
                        }}
                        style={{ marginTop: '0.75rem' }}
                        type="button"
                      >
                        Edit service
                      </button>
                    </article>
                  ))
                ) : (
                  <div className="empty-state">
                    <p>No services published yet. Use the form above to publish your first service.</p>
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      ) : null}

      {adminMode ? (
        <div className="page-stack">
          <section className="panel">
            <SectionTitle eyebrow="Admin" title="Platform metrics" description="Marketplace visibility from admin and analytics endpoints." />
            <div className="stat-grid">
              <StatCard accent="sun" detail="Users" label="Total users" value={workspace.adminDashboard?.total_users || 0} />
              <StatCard accent="sea" detail="Bookings" label="Total bookings" value={workspace.adminDashboard?.total_bookings || 0} />
              <StatCard accent="leaf" detail="Revenue" label="Analytics revenue" value={formatCurrency(workspace.adminDashboard?.released_revenue || 0)} />
              <StatCard accent="violet" detail="Unread alerts" label="Notifications" value={workspace.unreadCount} />
            </div>
          </section>

          <section className="panel">
            <SectionTitle eyebrow="Admin" title="Users" description="Manage roles and activation state." />
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {workspace.adminUsers.map((adminUser) => (
                    <tr key={adminUser.uid}>
                      <td>
                        <strong>{adminUser.username}</strong>
                        <p>{adminUser.email}</p>
                      </td>
                      <td>
                        <select onChange={(event) => setAdminRoleDrafts((current) => ({ ...current, [adminUser.uid]: event.target.value }))} value={adminRoleDrafts[adminUser.uid] || adminUser.role}>
                          <option value="user">User</option>
                          <option value="provider">Provider</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                      <td><StatusPill status={adminUser.is_active ? 'completed' : 'cancelled'} /></td>
                      <td className="data-table__actions">
                        <button className="button button--ghost button--small" onClick={() => runAction('Updating role', () => authorizedRequest((token) => api.updateAdminUserRole(adminUser.uid, adminRoleDrafts[adminUser.uid] || adminUser.role, token)), { successMessage: 'Role updated.' })} type="button">Save role</button>
                        <button className="button button--ghost button--small" onClick={() => runAction('Updating status', () => authorizedRequest((token) => api.updateAdminUserStatus(adminUser.uid, !adminUser.is_active, token)), { successMessage: 'User status updated.' })} type="button">
                          {adminUser.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <SectionTitle eyebrow="Admin" title="Disputes" description="Respond to disputes and update their state." />
            <div className="stack-list">
              {workspace.adminDisputes.length ? (
                workspace.adminDisputes.map((dispute) => (
                  <article className="list-card list-card--column" key={dispute.uid}>
                    <div className="list-card__main">
                      <div className="list-card__title-row">
                        <h3>{dispute.reason}</h3>
                        <StatusPill status={dispute.status} />
                      </div>
                      <p>{dispute.description || 'No description provided.'}</p>
                    </div>
                    <label className="field">
                      <span>Admin response</span>
                      <textarea onChange={(event) => setDisputeResponses((current) => ({ ...current, [dispute.uid]: event.target.value }))} rows="3" value={disputeResponses[dispute.uid] || ''} />
                    </label>
                    <div className="list-card__actions">
                      <button className="button button--ghost button--small" onClick={() => runAction('Updating dispute', () => authorizedRequest((token) => api.resolveAdminDispute(dispute.uid, { admin_response: disputeResponses[dispute.uid] || '', status: 'under_review' }, token)), { successMessage: 'Dispute moved to under review.' })} type="button">Under review</button>
                      <button className="button button--ghost button--small" onClick={() => runAction('Updating dispute', () => authorizedRequest((token) => api.resolveAdminDispute(dispute.uid, { admin_response: disputeResponses[dispute.uid] || '', status: 'resolved' }, token)), { successMessage: 'Dispute resolved.' })} type="button">Resolve</button>
                      <button className="button button--danger button--small" onClick={() => runAction('Updating dispute', () => authorizedRequest((token) => api.resolveAdminDispute(dispute.uid, { admin_response: disputeResponses[dispute.uid] || '', status: 'rejected' }, token)), { successMessage: 'Dispute rejected.' })} type="button">Reject</button>
                    </div>
                  </article>
                ))
              ) : (
                <div className="empty-state"><p>No disputes waiting for review.</p></div>
              )}
            </div>
          </section>

          <div className="workspace-grid">
            <section className="panel">
              <SectionTitle eyebrow="Audit" title="Deleted bookings" description="Soft-deleted booking records." />
              <div className="mini-list">
                {workspace.deletedBookings.length ? (
                  workspace.deletedBookings.map((booking) => (
                    <article className="mini-list__item" key={booking.uid}>
                      <div>
                        <strong>{booking.uid}</strong>
                        <p>{booking.delete_reason || 'No reason provided.'}</p>
                      </div>
                      <StatusPill status={booking.status} />
                    </article>
                  ))
                ) : (
                  <div className="empty-state empty-state--compact"><p>No deleted bookings.</p></div>
                )}
              </div>
            </section>

            <section className="panel">
              <SectionTitle eyebrow="Audit" title="Deleted reviews" description="Soft-deleted review records." />
              <div className="mini-list">
                {workspace.deletedReviews.length ? (
                  workspace.deletedReviews.map((review) => (
                    <article className="mini-list__item" key={review.uid}>
                      <div>
                        <strong>{review.rating}/5</strong>
                        <p>{review.delete_reason || 'No reason provided.'}</p>
                      </div>
                      <span>{review.booking_id}</span>
                    </article>
                  ))
                ) : (
                  <div className="empty-state empty-state--compact"><p>No deleted reviews.</p></div>
                )}
              </div>
            </section>

            <section className="panel">
              <SectionTitle eyebrow="Roster" title="Providers" description="Registered providers in the marketplace." />
              <div className="mini-list">
                {workspace.adminProviders.length ? (
                  workspace.adminProviders.map((provider) => (
                    <article className="mini-list__item" key={provider.uid}>
                      <div>
                        <strong>{provider.business_name || 'Independent provider'}</strong>
                        <p>{provider.bio || 'No bio provided.'}</p>
                      </div>
                      <span>{provider.rating.toFixed(1)}</span>
                    </article>
                  ))
                ) : (
                  <div className="empty-state empty-state--compact"><p>No providers found.</p></div>
                )}
              </div>
            </section>
          </div>
        </div>
      ) : null}
    </div>
  )
}
