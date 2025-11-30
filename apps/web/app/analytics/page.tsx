'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { GlassCard } from '@/components/ui'
import { Navbar, Footer, PageShell, AuthWrapper } from '@/components/layout'
import { getCurrentUser } from '@/lib/supabaseClient'
import { signOut } from '@/lib/auth'
import { getAnalytics, AnalyticsData, AnalyticsTimeRange } from '@/lib/apiClient'

interface UserWithMetadata {
  email?: string
  id?: string
  user_metadata?: {
    display_name?: string
  }
}

// Stat card component for displaying key metrics
function StatCard({
  label,
  value,
  subValue,
  trend,
  icon,
}: {
  label: string
  value: string | number
  subValue?: string
  trend?: 'up' | 'down' | 'neutral'
  icon?: string
}) {
  return (
    <div className="bg-white/5 rounded-xl p-4 border border-white/10">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-white/50 text-sm">{label}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          {subValue && (
            <p className={`text-sm mt-1 ${
              trend === 'up' ? 'text-green-400' :
              trend === 'down' ? 'text-red-400' :
              'text-white/40'
            }`}>
              {subValue}
            </p>
          )}
        </div>
        {icon && <span className="text-2xl">{icon}</span>}
      </div>
    </div>
  )
}

// Progress bar component
function ProgressBar({
  label,
  value,
  total,
  color = 'purple',
}: {
  label: string
  value: number
  total: number
  color?: 'purple' | 'green' | 'red' | 'blue'
}) {
  const percentage = total > 0 ? (value / total) * 100 : 0
  const colorClasses = {
    purple: 'bg-purple-500',
    green: 'bg-green-500',
    red: 'bg-red-500',
    blue: 'bg-blue-500',
  }

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-white/70">{label}</span>
        <span className="text-white/50">{value} ({percentage.toFixed(1)}%)</span>
      </div>
      <div className="h-2 bg-white/10 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClasses[color]} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

// Simple bar chart component
function SimpleBarChart({
  data,
  maxItems = 7,
}: {
  data: Array<{ date: string; count: number }>
  maxItems?: number
}) {
  const chartData = data.slice(-maxItems)
  const maxCount = Math.max(...chartData.map(d => d.count), 1)

  return (
    <div className="flex items-end gap-2 h-32">
      {chartData.map((item, index) => (
        <div key={index} className="flex-1 flex flex-col items-center">
          <div
            className="w-full bg-purple-500/70 rounded-t transition-all duration-500 hover:bg-purple-400"
            style={{
              height: `${(item.count / maxCount) * 100}%`,
              minHeight: item.count > 0 ? '4px' : '0',
            }}
          />
          <span className="text-[10px] text-white/40 mt-1 truncate w-full text-center">
            {item.date.slice(5)}
          </span>
        </div>
      ))}
    </div>
  )
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`
  return `${(seconds / 3600).toFixed(1)}h`
}

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
  return num.toString()
}

function AnalyticsContent() {
  const router = useRouter()
  const [user, setUser] = useState<UserWithMetadata | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState<AnalyticsTimeRange>('month')
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)

  useEffect(() => {
    const fetchUser = async () => {
      const currentUser = await getCurrentUser()
      setUser(currentUser as UserWithMetadata)
    }
    fetchUser()
  }, [])

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await getAnalytics(timeRange)
        setAnalytics(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics')
      } finally {
        setLoading(false)
      }
    }
    fetchAnalytics()
  }, [timeRange])

  const handleLogout = async () => {
    await signOut()
    router.push('/')
  }

  const timeRangeOptions: { value: AnalyticsTimeRange; label: string }[] = [
    { value: 'day', label: 'Last 24 Hours' },
    { value: 'week', label: 'Last 7 Days' },
    { value: 'month', label: 'Last 30 Days' },
    { value: 'year', label: 'Last Year' },
    { value: 'all_time', label: 'All Time' },
  ]

  return (
    <>
      <Navbar user={user} onLogout={handleLogout} />

      <PageShell
        title="Analytics"
        subtitle="Track your audiobook creation metrics"
      >
        {/* Time Range Selector */}
        <div className="mb-6 flex flex-wrap gap-2">
          {timeRangeOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setTimeRange(option.value)}
              className={`px-4 py-2 rounded-lg text-sm transition-all ${
                timeRange === option.value
                  ? 'bg-purple-600 text-white'
                  : 'bg-white/5 text-white/60 hover:bg-white/10 hover:text-white'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="bg-white/5 rounded-xl p-4 border border-white/10 animate-pulse">
                <div className="h-4 bg-white/10 rounded w-1/2 mb-2" />
                <div className="h-8 bg-white/10 rounded w-3/4" />
              </div>
            ))}
          </div>
        ) : error ? (
          <GlassCard>
            <div className="text-center py-8">
              <div className="text-4xl mb-4">!</div>
              <h3 className="text-lg font-semibold text-red-400 mb-2">Error Loading Analytics</h3>
              <p className="text-white/60 mb-4">{error}</p>
              <button
                onClick={() => setTimeRange(timeRange)}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Retry
              </button>
            </div>
          </GlassCard>
        ) : analytics ? (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                label="Total Jobs"
                value={analytics.total_jobs}
                icon="📊"
              />
              <StatCard
                label="Success Rate"
                value={`${analytics.success_rate}%`}
                trend={analytics.success_rate >= 80 ? 'up' : analytics.success_rate >= 50 ? 'neutral' : 'down'}
                icon="✅"
              />
              <StatCard
                label="Audio Generated"
                value={`${analytics.total_audio_minutes.toFixed(1)} min`}
                icon="🎧"
              />
              <StatCard
                label="Words Processed"
                value={formatNumber(analytics.total_words_processed)}
                icon="📝"
              />
            </div>

            {/* Jobs Overview & Processing Stats */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Jobs by Status */}
              <GlassCard title="Jobs Overview">
                <div className="space-y-4">
                  <ProgressBar
                    label="Completed"
                    value={analytics.completed_jobs}
                    total={analytics.total_jobs}
                    color="green"
                  />
                  <ProgressBar
                    label="In Progress"
                    value={analytics.pending_jobs}
                    total={analytics.total_jobs}
                    color="blue"
                  />
                  <ProgressBar
                    label="Failed"
                    value={analytics.failed_jobs}
                    total={analytics.total_jobs}
                    color="red"
                  />
                </div>
                <div className="mt-4 pt-4 border-t border-white/10 grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-green-400 text-xl font-bold">{analytics.completed_jobs}</p>
                    <p className="text-white/40 text-xs">Completed</p>
                  </div>
                  <div>
                    <p className="text-blue-400 text-xl font-bold">{analytics.pending_jobs}</p>
                    <p className="text-white/40 text-xs">In Progress</p>
                  </div>
                  <div>
                    <p className="text-red-400 text-xl font-bold">{analytics.failed_jobs}</p>
                    <p className="text-white/40 text-xs">Failed</p>
                  </div>
                </div>
              </GlassCard>

              {/* Processing Time Stats */}
              <GlassCard title="Processing Time">
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-3 bg-white/5 rounded-lg">
                    <p className="text-white/50 text-xs">Average</p>
                    <p className="text-white text-lg font-semibold">
                      {formatDuration(analytics.avg_processing_time_seconds)}
                    </p>
                  </div>
                  <div className="text-center p-3 bg-white/5 rounded-lg">
                    <p className="text-white/50 text-xs">Fastest</p>
                    <p className="text-green-400 text-lg font-semibold">
                      {formatDuration(analytics.min_processing_time_seconds)}
                    </p>
                  </div>
                  <div className="text-center p-3 bg-white/5 rounded-lg">
                    <p className="text-white/50 text-xs">Slowest</p>
                    <p className="text-orange-400 text-lg font-semibold">
                      {formatDuration(analytics.max_processing_time_seconds)}
                    </p>
                  </div>
                </div>
                <div className="p-3 bg-white/5 rounded-lg">
                  <p className="text-white/50 text-xs mb-1">Avg Audio Duration</p>
                  <p className="text-white text-lg font-semibold">
                    {analytics.avg_audio_duration_minutes.toFixed(1)} minutes
                  </p>
                </div>
              </GlassCard>
            </div>

            {/* Jobs Over Time Chart */}
            {analytics.jobs_by_day.length > 0 && (
              <GlassCard title="Jobs Created Over Time">
                <SimpleBarChart data={analytics.jobs_by_day} maxItems={14} />
              </GlassCard>
            )}

            {/* Popular Voices & Languages */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Popular Voices */}
              <GlassCard title="Popular Voices">
                {analytics.popular_voices.length > 0 ? (
                  <div className="space-y-3">
                    {analytics.popular_voices.slice(0, 5).map((voice, index) => (
                      <div key={voice.voice_id} className="flex items-center gap-3">
                        <span className="text-white/30 text-sm w-4">{index + 1}</span>
                        <div className="flex-1">
                          <p className="text-white text-sm truncate">{voice.voice_id}</p>
                          <div className="h-1.5 bg-white/10 rounded-full mt-1">
                            <div
                              className="h-full bg-purple-500 rounded-full"
                              style={{ width: `${voice.percentage}%` }}
                            />
                          </div>
                        </div>
                        <span className="text-white/50 text-xs">{voice.count}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-white/40 text-center py-4">No voice data yet</p>
                )}
              </GlassCard>

              {/* Input Languages */}
              <GlassCard title="Input Languages">
                {analytics.popular_input_languages.length > 0 ? (
                  <div className="space-y-3">
                    {analytics.popular_input_languages.map((lang, index) => (
                      <div key={lang.language} className="flex items-center gap-3">
                        <span className="text-white/30 text-sm w-4">{index + 1}</span>
                        <div className="flex-1">
                          <p className="text-white text-sm">{lang.language.toUpperCase()}</p>
                          <div className="h-1.5 bg-white/10 rounded-full mt-1">
                            <div
                              className="h-full bg-blue-500 rounded-full"
                              style={{ width: `${lang.percentage}%` }}
                            />
                          </div>
                        </div>
                        <span className="text-white/50 text-xs">{lang.percentage}%</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-white/40 text-center py-4">No language data yet</p>
                )}
              </GlassCard>

              {/* Output Languages */}
              <GlassCard title="Output Languages">
                {analytics.popular_output_languages.length > 0 ? (
                  <div className="space-y-3">
                    {analytics.popular_output_languages.map((lang, index) => (
                      <div key={lang.language} className="flex items-center gap-3">
                        <span className="text-white/30 text-sm w-4">{index + 1}</span>
                        <div className="flex-1">
                          <p className="text-white text-sm">{lang.language.toUpperCase()}</p>
                          <div className="h-1.5 bg-white/10 rounded-full mt-1">
                            <div
                              className="h-full bg-green-500 rounded-full"
                              style={{ width: `${lang.percentage}%` }}
                            />
                          </div>
                        </div>
                        <span className="text-white/50 text-xs">{lang.percentage}%</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-white/40 text-center py-4">No language data yet</p>
                )}
              </GlassCard>
            </div>

            {/* Error Statistics */}
            {analytics.failed_jobs > 0 && (
              <GlassCard title="Error Analysis">
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <p className="text-red-400 text-2xl font-bold">{analytics.error_rate}%</p>
                    <p className="text-white/40 text-xs">Error Rate</p>
                  </div>
                  <p className="text-white/60 text-sm">
                    {analytics.failed_jobs} of {analytics.total_jobs} jobs failed
                  </p>
                </div>
                {analytics.common_errors.length > 0 && (
                  <div>
                    <h4 className="text-white/70 text-sm mb-2">Common Errors</h4>
                    <div className="space-y-2">
                      {analytics.common_errors.map((err, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-2 bg-white/5 rounded-lg"
                        >
                          <span className="text-white/70 text-sm truncate flex-1">
                            {err.error}
                          </span>
                          <span className="text-red-400 text-sm ml-2">{err.count}x</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </GlassCard>
            )}

            {/* Admin Stats (if available) */}
            {analytics.unique_users > 0 && (
              <GlassCard title="Platform Statistics (Admin)">
                <div className="grid grid-cols-2 gap-4">
                  <StatCard
                    label="Unique Users"
                    value={analytics.unique_users}
                    icon="👥"
                  />
                  <StatCard
                    label="New Users"
                    value={analytics.new_users_in_period}
                    subValue={`in selected period`}
                    icon="🆕"
                  />
                </div>
              </GlassCard>
            )}
          </div>
        ) : null}
      </PageShell>

      <Footer user={user} />
    </>
  )
}

export default function AnalyticsPage() {
  return (
    <AuthWrapper>
      <AnalyticsContent />
    </AuthWrapper>
  )
}
