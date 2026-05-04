const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v2'
).replace(/\/$/, '')

async function request(path, options = {}) {
  const { method = 'GET', token, body, params } = options
  const url = new URL(`${API_BASE_URL}${path}`)

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, value)
      }
    })
  }

  const headers = {
    Accept: 'application/json',
  }

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  const contentType = response.headers.get('content-type') || ''
  const responseData = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    let detail = responseData?.detail
    const errorMessage =
      typeof responseData === 'string'
        ? responseData
        : Array.isArray(detail)
          ? detail[0]?.msg || 'Validation error'
          : detail || response.statusText || 'Request failed'

    const error = new Error(errorMessage)
    error.status = response.status
    error.data = responseData
    throw error
  }

  return responseData
}

export const api = {
  // ── Auth ────────────────────────────────────────────────────────────────────

  login(payload) {
    return request('/auth/login', { method: 'POST', body: payload })
  },

  register(payload) {
    return request('/auth/register', { method: 'POST', body: payload })
  },

  verifyAccount(token) {
    return request(`/auth/verify/${token}`)
  },

  refreshToken(refreshToken) {
    return request('/auth/refresh-token', {
      method: 'POST',
      token: refreshToken,
    })
  },

  logout(token) {
    return request('/auth/logout', { method: 'POST', token })
  },

  getMe(token) {
    return request('/auth/me', { token })
  },

  // ── Services ────────────────────────────────────────────────────────────────

  getServices() {
    return request('/services/')
  },

  createService(payload, token) {
    return request('/services/', { method: 'POST', token, body: payload })
  },

  updateService(serviceId, payload, token) {
    return request(`/services/${serviceId}`, { method: 'PUT', token, body: payload })
  },

  deleteService(serviceId, token) {
    return request(`/services/${serviceId}`, { method: 'DELETE', token })
  },

  getProviderServices(providerId) {
    return request(`/services/provider/${providerId}`)
  },

  // ── Providers ───────────────────────────────────────────────────────────────

  getProviders() {
    return request('/providers/')
  },

  getMyProvider(userId, token) {
    return request(`/providers/${userId}`, { token })
  },

  createProvider(payload, token) {
    return request('/providers/', { method: 'POST', token, body: payload })
  },

  updateProvider(userId, payload, token) {
    return request(`/providers/${userId}`, { method: 'PUT', token, body: payload })
  },

  // ── Bookings ────────────────────────────────────────────────────────────────

  createBooking(payload, token) {
    return request('/bookings/', { method: 'POST', token, body: payload })
  },

  getMyBookings(token) {
    return request('/bookings/my-bookings', { token })
  },

  getProviderBookings(token) {
    return request('/bookings/provider-bookings', { token })
  },

  updateBookingStatus(bookingId, statusValue, token) {
    return request(`/bookings/${bookingId}/status`, {
      method: 'PATCH',
      token,
      body: { status: statusValue },
    })
  },

  cancelBooking(bookingId, token, reason) {
    return request(`/bookings/${bookingId}/cancel`, {
      method: 'PATCH',
      token,
      body: { delete_reason: reason || null },
    })
  },

  // ── Payments ────────────────────────────────────────────────────────────────

  createPayment(payload, token) {
    return request('/payments/', { method: 'POST', token, body: payload })
  },

  getPayment(paymentId, token) {
    return request(`/payments/${paymentId}`, { token })
  },

  // ── Reviews ─────────────────────────────────────────────────────────────────

  getReviews() {
    return request('/reviews/')
  },

  createReview(payload, token) {
    return request('/reviews/', { method: 'POST', token, body: payload })
  },

  // ── Notifications ───────────────────────────────────────────────────────────

  getNotifications(token) {
    return request('/notifications/', { token })
  },

  getUnreadNotifications(token) {
    return request('/notifications/unread', { token })
  },

  markNotificationRead(notificationId, token) {
    return request(`/notifications/${notificationId}/read`, {
      method: 'PATCH',
      token,
    })
  },

  markAllNotificationsRead(token) {
    return request('/notifications/read-all', {
      method: 'PATCH',
      token,
    })
  },

  // ── Analytics ───────────────────────────────────────────────────────────────

  getAnalyticsDashboard(token) {
    return request('/admin/dashboard', { token })
  },

  // ── Admin ────────────────────────────────────────────────────────────────────

  getAdminDashboard(token) {
    return request('/admin/dashboard', { token })
  },

  getAdminUsers(token) {
    return request('/admin/users', { token })
  },

  updateAdminUserStatus(userId, isActive, token) {
    return request(`/admin/users/${userId}/status`, {
      method: 'PATCH',
      token,
      body: { is_active: isActive },
    })
  },

  updateAdminUserRole(userId, role, token) {
    return request(`/admin/users/${userId}/role`, {
      method: 'PATCH',
      token,
      body: { role },
    })
  },

  getAdminDisputes(token) {
    return request('/admin/disputes', { token })
  },

  resolveAdminDispute(disputeId, payload, token) {
    return request(`/admin/disputes/${disputeId}/resolve`, {
      method: 'PATCH',
      token,
      body: payload,
    })
  },

  getDeletedBookings(token) {
    return request('/admin/audits/deleted-bookings', { token })
  },

  getDeletedReviews(token) {
    return request('/admin/audits/deleted-reviews', { token })
  },

  getAdminProviders(token) {
    return request('/admin/providers', { token })
  },
}
