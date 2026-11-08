import { api } from './client'
import type { Simulation, SimulationInput } from './types'

export const projectionsApi = {
  simulate: (input: SimulationInput) =>
    api
      .post<{ simulation: Simulation }>('/projections/simulate', input)
      .then((r) => r.simulation),
}