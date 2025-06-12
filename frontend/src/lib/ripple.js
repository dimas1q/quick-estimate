export function initRipple() {
  document.addEventListener('click', (e) => {
    const target = e.target.closest('.qe-btn, .qe-btn-secondary, .qe-btn-danger, .qe-btn-success, .qe-btn-warning')
    if (!target) return
    const rect = target.getBoundingClientRect()
    const size = Math.max(target.offsetWidth, target.offsetHeight)
    const ripple = document.createElement('span')
    ripple.className = 'qe-ripple'
    ripple.style.width = ripple.style.height = `${size}px`
    ripple.style.left = `${e.clientX - rect.left - size / 2}px`
    ripple.style.top = `${e.clientY - rect.top - size / 2}px`
    target.appendChild(ripple)
    ripple.addEventListener('animationend', () => ripple.remove())
  })
}
