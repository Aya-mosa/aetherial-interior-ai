const key = process.argv[2] || process.env.OPENROUTER_API_KEY

if (!key) {
  console.error('Usage: node check_credits.js <OR_API_KEY>')
  process.exit(1)
}

fetch('https://openrouter.ai/api/v1/credits', {
  headers: { 'Authorization': `Bearer ${key}` }
})
.then(r => r.json())
.then(data => {
  const total   = data.data?.total_credits  ?? data.total_credits  ?? '?'
  const used    = data.data?.total_usage    ?? data.total_usage    ?? '?'
  const remaining = (typeof total === 'number' && typeof used === 'number')
    ? (total - used).toFixed(4)
    : '?'

  console.log('\n╔══════════════════════════════╗')
  console.log('║   OpenRouter Credits Check   ║')
  console.log('╠══════════════════════════════╣')
  console.log(`║  Total:     $${String(total).padEnd(16)}║`)
  console.log(`║  Used:      $${String(used).padEnd(16)}║`)
  console.log(`║  Remaining: $${String(remaining).padEnd(16)}║`)
  console.log('╠══════════════════════════════╣')

  const rem = parseFloat(remaining)
  if (isNaN(rem)) {
    console.log('║  Status:    ⚠️  Unknown        ║')
  } else if (rem <= 0) {
    console.log('║  Status:    ❌ No credits!     ║')
    console.log('║  → openrouter.ai/credits      ║')
  } else if (rem < 1) {
    console.log('║  Status:    ⚠️  Low balance!   ║')
    console.log('║  → Consider recharging        ║')
  } else {
    console.log('║  Status:    ✅ Sufficient      ║')
  }
  console.log('╚══════════════════════════════╝\n')
})
.catch(e => console.error('Error:', e.message))
