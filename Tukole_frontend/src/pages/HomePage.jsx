import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { SectionTitle } from '../components/SectionTitle'
import { StatCard } from '../components/StatCard'
import { StatusPill } from '../components/StatusPill'
import { useAuth } from '../context/AuthContext'

function formatCurrency(value) {
  return new Intl.NumberFormat('en-UG', {
    style: 'currency',
    currency: 'UGX',
    maximumFractionDigits: 0,
  }).format(Number(value || 0))
}

export default function HomePage() {
  const { isAuthenticated } = useAuth()
  const [services, setServices] = useState([])
  const [providers, setProviders] = useState([])
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadLandingData() {
      try {
        const [serviceResponse, providerResponse, reviewResponse] = await Promise.all([
          api.getServices(),
          api.getProviders(),
          api.getReviews(),
        ])

        setServices(serviceResponse)
        setProviders(providerResponse)
        setReviews(reviewResponse)
      } catch (requestError) {
        setError(requestError.message)
      } finally {
        setLoading(false)
      }
    }

    loadLandingData()
  }, [])

  const featuredServices = services.slice(0, 6)
  const featuredProviders = providers.slice(0, 4)
  const providerAverage = providers.length
    ? (
        providers.reduce((total, provider) => total + Number(provider.rating || 0), 0) /
        providers.length
      ).toFixed(1)
    : '0.0'

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <div className="hero-panel__copy">
          <p className="eyebrow">Tukole marketplace</p>
          <h1>Beautiful service booking for users, providers, and admins.</h1>
          <p className="hero-panel__text">
            Tukole brings together discovery, booking, payments, reviews, disputes, and
            operations in one warm, modern frontend built for your FastAPI backend.
          </p>

          <div className="hero-panel__actions">
            <Link className="button" to={isAuthenticated ? '/workspace' : '/auth'}>
              {isAuthenticated ? 'Open workspace' : 'Start with Tukole'}
            </Link>
            <a className="button button--ghost" href="#featured-services">
              Explore services
            </a>
          </div>
        </div>

        <div className="hero-panel__spotlight">
          <div className="spotlight-card">
            <p className="spotlight-card__eyebrow">Why this frontend works</p>
            <h2>One interface for the whole marketplace journey.</h2>
            <div className="spotlight-list">
              <article>
                <strong>Customers</strong>
                <p>Browse services, book quickly, pay the right amount, and stay updated.</p>
              </article>
              <article>
                <strong>Providers</strong>
                <p>Create a profile, publish services, and manage every booking status.</p>
              </article>
              <article>
                <strong>Admins</strong>
                <p>See platform metrics, resolve disputes, and keep the marketplace healthy.</p>
              </article>
            </div>
          </div>
        </div>
      </section>

      <div className="stat-grid">
        <StatCard
          accent="sun"
          detail="Public offerings connected to your backend"
          label="Live services"
          value={loading ? '...' : services.length}
        />
        <StatCard
          accent="sea"
          detail="Provider profiles ready for bookings"
          label="Providers"
          value={loading ? '...' : providers.length}
        />
        <StatCard
          accent="leaf"
          detail="Average provider rating from the current data"
          label="Trust score"
          value={loading ? '...' : providerAverage}
        />
        <StatCard
          accent="violet"
          detail="Community feedback already visible to visitors"
          label="Reviews"
          value={loading ? '...' : reviews.length}
        />
      </div>

      {error ? <div className="feedback feedback--error">{error}</div> : null}

      <section className="panel panel--story">
        <SectionTitle
          eyebrow="Built to convert"
          title="A calmer, more premium first impression"
          description="This frontend leans into warm typography, layered color, and focused workflows so Tukole feels like a product, not just a collection of forms."
        />
        <div className="story-grid">
          <article className="story-card">
            <h3>Clear discovery</h3>
            <p>Visitors immediately understand what Tukole offers and where to go next.</p>
          </article>
          <article className="story-card">
            <h3>Role-aware workspace</h3>
            <p>The dashboard adapts to users, providers, and admins without feeling cluttered.</p>
          </article>
          <article className="story-card">
            <h3>API-first integration</h3>
            <p>Every important surface is connected to your existing routes instead of mock-only UI.</p>
          </article>
        </div>
      </section>

      <section className="panel" id="featured-services">
        <SectionTitle
          eyebrow="Featured services"
          title="What people can book right now"
          description="This section reads live service records from your `/services` endpoint."
          action={
            <Link className="button button--ghost" to={isAuthenticated ? '/workspace' : '/auth'}>
              Book from workspace
            </Link>
          }
        />

        <div className="card-grid">
          {featuredServices.length ? (
            featuredServices.map((service) => (
              <article className="service-card" key={service.uid}>
                <div className="service-card__top">
                  <StatusPill status="pending" />
                  <span className="service-card__price">{formatCurrency(service.price)}</span>
                </div>
                <h3>{service.name}</h3>
                <p>{service.description || 'A dependable marketplace service ready to be booked.'}</p>
              </article>
            ))
          ) : (
            <div className="empty-state">
              <h3>No services yet</h3>
              <p>As soon as your backend has services, they will appear here automatically.</p>
            </div>
          )}
        </div>
      </section>

      <section className="panel">
        <SectionTitle
          eyebrow="Provider roster"
          title="People powering the marketplace"
          description="Live provider records from the Tukole API help the landing page feel active and trustworthy."
        />

        <div className="provider-grid">
          {featuredProviders.length ? (
            featuredProviders.map((provider) => (
              <article className="provider-card" key={provider.uid}>
                <div className="provider-card__badge">
                  <StatusPill status="provider" />
                  <span>{provider.rating.toFixed(1)} / 5</span>
                </div>
                <h3>{provider.business_name || 'Independent provider'}</h3>
                <p>{provider.bio || 'Available to help customers with high-quality service delivery.'}</p>
              </article>
            ))
          ) : (
            <div className="empty-state">
              <h3>No providers yet</h3>
              <p>Create a provider profile from the workspace to bring this section to life.</p>
            </div>
          )}
        </div>
      </section>

      <section className="panel">
        <SectionTitle
          eyebrow="Flow"
          title="How Tukole moves work from discovery to delivery"
          description="The frontend is structured around the same marketplace lifecycle your backend already supports."
        />

        <div className="steps-grid">
          <article className="step-card">
            <span>01</span>
            <h3>Discover and book</h3>
            <p>Customers browse services and submit bookings with a clean scheduling form.</p>
          </article>
          <article className="step-card">
            <span>02</span>
            <h3>Manage and fulfill</h3>
            <p>Providers update their profile, publish offers, and close out bookings from one studio.</p>
          </article>
          <article className="step-card">
            <span>03</span>
            <h3>Operate with confidence</h3>
            <p>Admins can watch the marketplace, handle disputes, and inspect deleted records when needed.</p>
          </article>
        </div>
      </section>
    </div>
  )
}
