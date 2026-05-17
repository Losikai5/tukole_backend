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

  const categories = [
    { count: '48 providers', href: '#featured-services', icon: '🪠', name: 'Plumbing' },
    { count: '35 providers', href: '#featured-services', icon: '💡', name: 'Electrical' },
    { count: '62 providers', href: '#featured-services', icon: '🧹', name: 'Cleaning' },
    { count: '24 providers', href: '#featured-services', icon: '🎨', name: 'Painting' },
    { count: '18 providers', href: '#featured-services', icon: '🚚', name: 'Moving' },
    { count: '31 providers', href: '#featured-services', icon: '🏠', name: 'Renovation' },
  ]

  const features = [
    {
      description: 'Every provider is reviewed before they appear in the marketplace.',
      icon: '✓',
      title: 'Verified providers',
    },
    {
      description: 'Payments are handled through the backend flow you already use.',
      icon: '₿',
      title: 'Escrow payments',
    },
    {
      description: 'Customers can compare feedback before choosing a provider.',
      icon: '★',
      title: 'Reviews and ratings',
    },
    {
      description: 'The layout stays fast and readable on smaller phones.',
      icon: '⌁',
      title: 'Mobile-first',
    },
  ]

  const steps = [
    {
      description: 'Browse verified providers by category and location.',
      index: '01',
      title: 'Search',
    },
    {
      description: 'Compare profiles, prices, and reviews.',
      index: '02',
      title: 'Choose',
    },
    {
      description: 'Book a service and pay securely.',
      index: '03',
      title: 'Book',
    },
    {
      description: 'Confirm the work and complete payment.',
      index: '04',
      title: 'Confirm',
    },
  ]

  return (
    <div className="page-stack page-stack--landing">
      <section className="hero-panel hero-panel--marketplace">
        <div className="hero-panel__copy">
          <p className="eyebrow">🇺🇬 Made for Uganda</p>
          <h1>Find trusted service providers near you</h1>
          <p className="hero-panel__text">
            Tukole connects you with verified plumbers, electricians, cleaners, and more - with
            secure mobile money payments.
          </p>

          <div className="hero-panel__actions">
            <a className="button" href="#popular-categories">
              Browse Services
            </a>
            <Link className="button button--ghost" to="/auth?mode=register&role=provider">
              Become a Provider
            </Link>
          </div>

          <p className="hero-panel__note">
            <strong>&quot;Tukole&quot;</strong> means <em>&quot;Let us work&quot;</em> in Luganda.
          </p>
        </div>

        <div className="hero-panel__spotlight">
          <div className="hero-scene">
            <div className="hero-scene__image" aria-hidden="true">
              <div className="hero-scene__glow hero-scene__glow--one" />
              <div className="hero-scene__glow hero-scene__glow--two" />
              <div className="hero-scene__card hero-scene__card--top">
                <span>Verified providers</span>
                <strong>{loading ? '...' : providers.length}</strong>
              </div>
              <div className="hero-scene__card hero-scene__card--middle">
                <span>Live services</span>
                <strong>{loading ? '...' : services.length}</strong>
              </div>
              <div className="hero-scene__card hero-scene__card--bottom">
                <span>Community reviews</span>
                <strong>{loading ? '...' : reviews.length}</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="stat-grid">
        <StatCard
          accent="sun"
          detail="Live offerings from the backend"
          label="Live services"
          value={loading ? '...' : services.length}
        />
        <StatCard
          accent="sea"
          detail="Provider profiles ready to book"
          label="Providers"
          value={loading ? '...' : providers.length}
        />
        <StatCard
          accent="leaf"
          detail="Average provider rating"
          label="Trust score"
          value={loading ? '...' : providerAverage}
        />
        <StatCard
          accent="violet"
          detail="Visible community feedback"
          label="Reviews"
          value={loading ? '...' : reviews.length}
        />
      </div>

      {error ? <div className="feedback feedback--error">{error}</div> : null}

      <section className="panel panel--story">
        <SectionTitle
          eyebrow="Why Tukole?"
          title="A simpler way to find trusted help"
          description="No more WhatsApp groups and word of mouth. Tukole brings trust, security, and convenience to the marketplace."
        />
        <div className="feature-grid">
          {features.map((feature) => (
            <article className="feature-card" key={feature.title}>
              <span className="feature-card__icon" aria-hidden="true">
                {feature.icon}
              </span>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel" id="popular-categories">
        <SectionTitle
          eyebrow="Popular categories"
          title="Find skilled professionals"
          description="Browse the most common service types in Kampala and beyond."
        />

        <div className="category-grid">
          {categories.map((category) => (
            <a className="category-card" href={category.href} key={category.name}>
              <span className="category-card__icon" aria-hidden="true">
                {category.icon}
              </span>
              <strong>{category.name}</strong>
              <span>{category.count}</span>
            </a>
          ))}
        </div>
      </section>

      <section className="panel" id="featured-services">
        <SectionTitle
          eyebrow="Featured services"
          title="What people can book now"
          description="Live service records from your backend appear here."
          action={
            <Link className="button button--ghost" to={isAuthenticated ? '/workspace' : '/auth'}>
              Get started
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
              <p>Services will appear here once the backend has them.</p>
            </div>
          )}
        </div>
      </section>

      <section className="panel">
        <SectionTitle
          eyebrow="How it works"
          title="Getting quality service is simple"
          description="The flow is short, clear, and built for mobile users."
        />

        <div className="steps-grid steps-grid--wide">
          {steps.map((step) => (
            <article className="step-card" key={step.index}>
              <span>{step.index}</span>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel cta-band">
        <div>
          <p className="eyebrow">Ready to Tukole?</p>
          <h2>Join Uganda&apos;s service marketplace.</h2>
          <p>Whether you need help or want to offer it, Tukole keeps the next step simple.</p>
        </div>
        <div className="cta-band__actions">
          <Link className="button" to={isAuthenticated ? '/workspace' : '/auth'}>
            Get Started
          </Link>
          <Link className="button button--ghost" to="/auth?mode=register&role=provider">
            List Your Services
          </Link>
        </div>
      </section>

      <section className="panel">
        <SectionTitle
          eyebrow="Provider roster"
          title="People powering the marketplace"
          description="Live provider records keep the page active."
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
              <p>Create a provider profile in the workspace.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
