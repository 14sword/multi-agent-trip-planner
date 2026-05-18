export interface Location {
  longitude: number
  latitude: number
}

export interface Attraction {
  name: string
  address: string
  location?: Location
  visit_duration: number
  description: string
  category?: string
  rating?: number
  image_url?: string
  ticket_price?: number
}

export interface Meal {
  type: string
  name: string
  address?: string
  location?: Location
  description?: string
  estimated_cost: number
}

export interface Hotel {
  name: string
  address: string
  location?: Location
  price_range: string
  rating?: number
  distance: string
  type: string
  estimated_cost: number
}

export interface TransportInfo {
  departure_city: string
  destination_city: string
  recommended_mode: string
  estimated_cost: number
  estimated_duration: string
  notes: string
  arrival_longitude?: number
  arrival_latitude?: number
}

export interface Budget {
  total_attractions: number
  total_hotels: number
  total_meals: number
  total_transportation: number
  total: number
}

export interface DayPlan {
  date: string
  day_index: number
  description: string
  transportation?: string
  accommodation?: string
  hotel?: Hotel
  attractions: Attraction[]
  meals: Meal[]
}

export interface WeatherInfo {
  date: string
  day_weather: string
  night_weather: string
  day_temp: number
  night_temp: number
  wind_direction: string
  wind_power: string
}

export interface CpsLink {
  name: string
  url: string
}

export interface TripPlan {
  id?: string
  city: string
  departure_city?: string
  start_date: string
  end_date: string
  days: DayPlan[]
  weather_info: WeatherInfo[]
  overall_suggestions: string
  budget?: Budget
  transport_info?: TransportInfo
  share_token?: string
  cps_links?: Record<string, CpsLink>
}

export interface TripPlanRequest {
  city: string
  departure_city: string
  start_date: string
  end_date: string
  days: number
  travelers: number
  preferences: string[]
  extra_info?: string
  budget: string
  transportation: string
  accommodation: string
}
