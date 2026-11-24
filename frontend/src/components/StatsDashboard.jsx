// StatsDashboard: the user's usage numbers as a row of three stat tiles.
// No chart: each stat is a single number, so the number itself is the figure.
// Each tile = a label (what it is), the value, and a one-line hint (what it counts).
// Big values are shortened (12,900 -> 12.9K); the exact number shows on hover.

const exact = new Intl.NumberFormat('en-US')
const compact = new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 })
const oneDecimal = new Intl.NumberFormat('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })

function formatCount(value) {
  return value >= 10000 ? compact.format(value) : exact.format(value)
}

export default function StatsDashboard({ stats }) {
  const tiles = [
    {
      label: 'Conversations',
      value: formatCount(stats.total_conversations),
      exact: exact.format(stats.total_conversations),
      hint: 'Chats you have started',
    },
    {
      label: 'Tokens used',
      value: formatCount(stats.total_tokens),
      exact: exact.format(stats.total_tokens),
      hint: 'Your questions (with the documents sent along) and the answers',
    },
    {
      label: 'Average tokens per message',
      value: oneDecimal.format(stats.avg_tokens_per_message),
      exact: oneDecimal.format(stats.avg_tokens_per_message),
      hint: 'Across every message with a token count',
    },
  ]

  return (
    <dl className="stat-row">
      {tiles.map((tile) => (
        <div className="stat-tile" key={tile.label}>
          <dt className="stat-tile__label">{tile.label}</dt>
          <dd className="stat-tile__value" title={tile.exact}>
            {tile.value}
          </dd>
          <dd className="stat-tile__hint">{tile.hint}</dd>
        </div>
      ))}
    </dl>
  )
}
