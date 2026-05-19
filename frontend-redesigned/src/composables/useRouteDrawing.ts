/**
 * useRouteDrawing — 地图路线绘制 composable
 * 从 Result.vue 的 initMap 提取，包含距离感知降级链 + 并发队列
 */
import type { Ref } from 'vue'

// Douglas-Peucker 路径简化
export function simplifyPath(pts: [number, number][], tolerance: number = 0.0005): [number, number][] {
  if (pts.length <= 2) return pts
  let maxDist = 0, maxIdx = 0
  const [sx, sy] = pts[0], [ex, ey] = pts[pts.length - 1]
  const dx = ex - sx, dy = ey - sy
  const lenSq = dx * dx + dy * dy
  for (let i = 1; i < pts.length - 1; i++) {
    const t = Math.max(0, Math.min(1, ((pts[i][0] - sx) * dx + (pts[i][1] - sy) * dy) / lenSq))
    const px = sx + t * dx, py = sy + t * dy
    const dist = Math.sqrt((pts[i][0] - px) ** 2 + (pts[i][1] - py) ** 2)
    if (dist > maxDist) { maxDist = dist; maxIdx = i }
  }
  if (maxDist > tolerance) {
    const left = simplifyPath(pts.slice(0, maxIdx + 1), tolerance)
    const right = simplifyPath(pts.slice(maxIdx), tolerance)
    return left.slice(0, -1).concat(right)
  }
  return [pts[0], pts[pts.length - 1]]
}

export function useRouteDrawing(params: {
  map: () => any
  tripPlan: () => any
  dayPoints: () => { pos: [number, number]; type: string; name: string; detail?: any }[][]
  dayPositions: [number, number][][]
  dayColors: string[]
  onRouteCompleted: () => void
}) {
  const segmentCache: Map<string, [number, number][]> = new Map()
  const drawnSegments: Set<string> = new Set()

  let totalSegments = 0
  let completedSegments = 0
  let routesReadyResolve: (() => void) | null = null
  let routesReady = new Promise<void>((r) => { routesReadyResolve = r })

  const recalcSegments = () => {
    totalSegments = 0
    params.dayPositions.forEach((positions) => {
      if (positions.length >= 2) totalSegments += positions.length - 1
    })
  }

  // 路线 API 并发队列
  const ROUTE_CONCURRENCY = 4
  let routeActive = 0
  const routeQueue: (() => void)[] = []

  const runRoute = (fn: () => void) => {
    if (routeActive < ROUTE_CONCURRENCY) {
      routeActive++
      fn()
    } else {
      routeQueue.push(fn)
    }
  }

  const routeDone = () => {
    routeActive--
    if (routeQueue.length > 0) {
      routeActive++
      routeQueue.shift()!()
    }
  }

  const routeDoneWithFitView = () => {
    completedSegments++
    routeDone()
    params.onRouteCompleted()
    if (completedSegments >= totalSegments) {
      routesReadyResolve?.()
      const m = params.map()
      if (m) setTimeout(() => { if (params.map()) params.map().setFitView(null, false, [60, 60, 60, 60]) }, 300)
    }
  }

  const drawRoute = (
    p0: [number, number], p1: [number, number],
    segKey: string, color: string,
    isMealSeg?: boolean, isArrivalSeg?: boolean, isReturnSeg?: boolean, isInterDaySeg?: boolean,
  ) => {
    const m = params.map()
    const tripPlan = params.tripPlan()
    if (!m) return

    // F1: 距离感知 → 自适应降级链
    const dLat = (p1[1] - p0[1]) * 111
    const dLng = (p1[0] - p0[0]) * 111 * Math.cos((p0[1] + p1[1]) / 2 * Math.PI / 180)
    const straightDist = Math.sqrt(dLat * dLat + dLng * dLng)

    const makeFallbackChain = (): string[] => {
      const isShort = straightDist < 0.5
      const isMedium = straightDist < 3
      if (isShort) return ['walking', 'driving', 'direct']
      if (isMedium) return ['driving', 'transit', 'walking', 'direct']
      return ['driving', 'transit', 'direct']
    }
    const fallbackModes = makeFallbackChain()
    let fallbackIdx = 0

    const addModeLabel = (path: [number, number][], mode: string) => {
      if (!m || path.length < 2) return
      const midIdx = Math.floor(path.length / 2)
      const mid = path[midIdx]
      let totalDist = 0
      for (let i = 1; i < path.length; i++) {
        const dx = (path[i][0] - path[i - 1][0]) * 111
        const dy = (path[i][1] - path[i - 1][1]) * 111
        totalDist += Math.sqrt(dx * dx + dy * dy)
      }
      const distText = totalDist < 1 ? `${Math.round(totalDist * 1000)}m` : `${totalDist.toFixed(1)}km`
      const speedMap: Record<string, number> = { driving: 40, walking: 5, direct: 30 }
      const estMin = Math.round(totalDist / (speedMap[mode] || 30) * 60)
      const timeText = estMin < 1 ? '<1分钟' : estMin > 60 ? `${Math.round(estMin / 60)}小时${estMin % 60}分` : `${estMin}分钟`

      const transportInfo = tripPlan?.transport_info
      let icon = '📍'
      let labelBg = 'white'
      let labelColor = '#555'
      if (isInterDaySeg) {
        icon = '🔄'; labelBg = '#f1f5f9'; labelColor = '#64748b'
      } else if (isArrivalSeg) {
        icon = transportInfo?.recommended_mode?.includes('飞机') ? '✈️' : '🚄'
        labelBg = '#eff6ff'; labelColor = '#3b82f6'
      } else if (isReturnSeg) {
        icon = '🏨'; labelBg = '#fffbeb'; labelColor = '#f59e0b'
      } else {
        const modeIcons: Record<string, string> = { driving: '🚗', walking: '🚶', direct: '📍' }
        icon = modeIcons[mode] || '📍'
        if (mode === 'direct') { labelBg = '#f8f9fa'; labelColor = '#999' }
      }

      const isDirect = mode === 'direct'
      const detailText = isDirect
        ? `<span style="color:#aaa;font-size:8px;">直线距离 · 无路径数据</span>`
        : `<span style="color:#999;">·</span><span style="color:#666;">${timeText}</span>`

      const modeMarker = new (window as any).AMap.Marker({
        position: new (window as any).AMap.LngLat(mid[0], mid[1]),
        content: `<div style="background:${labelBg};padding:3px 8px;border-radius:10px;font-size:9px;color:${labelColor};white-space:nowrap;box-shadow:0 1px 6px rgba(0,0,0,0.12);border:1px solid rgba(0,0,0,0.06);font-family:var(--font-body);font-weight:500;pointer-events:none;display:flex;align-items:center;gap:4px;">
          <span>${icon}</span>
          <span style="color:#333;font-weight:600;">${distText}</span>
          ${detailText}
        </div>`,
        offset: new (window as any).AMap.Pixel(-30, -8),
        zIndex: 80,
      })
      m.add(modeMarker)
    }

    const addPolyline = (path: [number, number][], opacity: number, mode?: string) => {
      if (!m || path.length === 0) return
      segmentCache.set(segKey, path)
      drawnSegments.add(segKey)

      const lineColor = isInterDaySeg ? '#94a3b8' : isArrivalSeg ? '#3b82f6' : color
      const glowWeight = isMealSeg ? 6 : isInterDaySeg ? 12 : 18
      const mainWeight = isMealSeg ? 3 : isInterDaySeg ? 4 : isArrivalSeg || isReturnSeg ? 5 : 6
      const mainOpacity = isMealSeg ? opacity * 0.7 : isInterDaySeg ? 0.6 : Math.min(opacity, 0.95)

      const AMap = (window as any).AMap
      m.add(new AMap.Polyline({
        path, strokeColor: lineColor, strokeWeight: glowWeight,
        strokeOpacity: isMealSeg ? 0.12 : 0.25, lineJoin: 'round', lineCap: 'round',
      }))

      let lineStyle: Record<string, any>
      if (isInterDaySeg) {
        lineStyle = { strokeStyle: 'dashed', strokeDasharray: [6, 8], showDir: false }
      } else if (isArrivalSeg || isReturnSeg) {
        lineStyle = { strokeStyle: 'dashed', strokeDasharray: [10, 6], showDir: false }
      } else {
        lineStyle = {
          driving: { showDir: false },
          walking: { strokeStyle: 'dashed', strokeDasharray: [8, 6], showDir: false },
          direct: { strokeStyle: 'dashed', strokeDasharray: [6, 8], showDir: false },
        }[mode || 'driving'] || { showDir: false }
      }
      m.add(new AMap.Polyline({
        path, strokeColor: lineColor, strokeWeight: mainWeight,
        strokeOpacity: mainOpacity, lineJoin: 'round', lineCap: 'round',
        ...lineStyle,
      }))
    }

    const tryBackendProxy = (fallbackMode: string = 'driving') => {
      if (drawnSegments.has(segKey)) { routeDoneWithFitView(); return }
      console.log(`[路线规划] 请求 ${segKey}: mode=${fallbackMode}`)
      const originStr = `${p0[0]},${p0[1]}`
      const destStr = `${p1[0]},${p1[1]}`
      const cityParam = encodeURIComponent(tripPlan?.city || '')
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 8000)
      fetch(`/api/trip/route?origin=${originStr}&destination=${destStr}&mode=${fallbackMode}&city=${cityParam}`, { signal: controller.signal })
        .then(r => {
          clearTimeout(timer)
          if (!r.ok) throw new Error(`HTTP ${r.status}`)
          return r.json()
        })
        .then((data: any) => {
          if (!params.map()) { routeDoneWithFitView(); return }
          if (data.path && data.path.length > 0) {
            const routeMode = data.mode || fallbackMode
            console.log(`[路线规划] ✓ ${segKey} 绘制成功: ${routeMode}, ${data.path.length}点`)
            addPolyline(data.path, 0.85, routeMode)
            if (!isMealSeg) addModeLabel(data.path, routeMode)
            routeDoneWithFitView()
          } else {
            fallbackIdx++
            if (fallbackIdx < fallbackModes.length) {
              console.warn(`[路线规划] ${fallbackMode} 空路径 (${segKey}) → 尝试 ${fallbackModes[fallbackIdx]}`)
              setTimeout(() => tryBackendProxy(fallbackModes[fallbackIdx]), 300)
            } else {
              console.warn(`[路线规划] 所有模式失败 (${segKey})，使用直线兜底`)
              addPolyline([p0, p1], 0.5, 'direct')
              routeDoneWithFitView()
            }
          }
        })
        .catch((err) => {
          clearTimeout(timer)
          console.warn(`[路线规划] 代理失败 (${segKey}, ${fallbackMode}):`, err?.message)
          fallbackIdx++
          if (fallbackIdx < fallbackModes.length) {
            setTimeout(() => tryBackendProxy(fallbackModes[fallbackIdx]), 300)
          } else {
            console.warn(`[路线规划] 所有模式异常 (${segKey})，使用直线兜底`)
            addPolyline([p0, p1], 0.5, 'direct')
            routeDoneWithFitView()
          }
        })
    }

    tryBackendProxy(fallbackModes[0])
  }

  const drawAllRoutes = () => {
    const dp = params.dayPoints()
    params.dayPositions.forEach((positions, dayIdx) => {
      if (positions.length < 2) return
      const color = params.dayColors[dayIdx % params.dayColors.length]
      const dayPts = dp[dayIdx] || []
      for (let i = 0; i < positions.length - 1; i++) {
        if (positions[i][0] === positions[i + 1][0] && positions[i][1] === positions[i + 1][1]) {
          routeDoneWithFitView()
          continue
        }
        const isMealSeg = dayPts[i]?.type === 'meal' || dayPts[i + 1]?.type === 'meal'
        const isArrivalSeg = dayPts[i]?.type === 'arrival'
        const isReturnSeg = dayPts[i + 1]?.type === 'hotel' && i === positions.length - 2
        runRoute(() => drawRoute(positions[i], positions[i + 1], `${dayIdx}-${i}`, color, isMealSeg, isArrivalSeg, isReturnSeg))
      }
    })
    // 跨天连接
    for (let d = 0; d < params.dayPositions.length - 1; d++) {
      const lastPos = params.dayPositions[d]
      const nextPos = params.dayPositions[d + 1]
      if (!lastPos?.length || !nextPos?.length) continue
      const from = lastPos[lastPos.length - 1]
      const to = nextPos[0]
      if (from[0] === to[0] && from[1] === to[1]) continue
      runRoute(() => drawRoute(from, to, `interday-${d}`, '#94a3b8', false, false, false, true))
    }
  }

  const getDayRoutes = () => {
    const routes: [number, number][][] = []
    params.dayPositions.forEach((positions, dayIdx) => {
      if (positions.length < 2) return
      const route: [number, number][] = []
      for (let i = 0; i < positions.length - 1; i++) {
        const seg = segmentCache.get(`${dayIdx}-${i}`)
        if (seg && seg.length > 0) {
          if (route.length > 0) {
            const last = route[route.length - 1]
            const start = seg[0]
            if (last[0] === start[0] && last[1] === start[1]) {
              route.push(...seg.slice(1))
            } else {
              route.push(...seg)
            }
          } else {
            route.push(...seg)
          }
        }
      }
      routes[dayIdx] = route
    })
    return routes
  }

  const cleanup = () => {
    segmentCache.clear()
    drawnSegments.clear()
    routeQueue.length = 0
  }

  // 地理编码后重置并重绘所有路线
  const resetAndRedraw = () => {
    segmentCache.clear()
    drawnSegments.clear()
    completedSegments = 0
    recalcSegments()
    routesReady = new Promise<void>((r) => { routesReadyResolve = r })
    drawAllRoutes()
  }

  // 不重建 promise 的重绘（仅 routesReady 已创建的情况）
  const redrawWithReady = () => {
    completedSegments = 0
    recalcSegments()
    drawAllRoutes()
  }

  recalcSegments()

  return {
    segmentCache,
    drawnSegments,
    getRoutesReady: () => routesReady,
    drawAllRoutes,
    getDayRoutes,
    resetAndRedraw,
    redrawWithReady,
    cleanup,
  }
}