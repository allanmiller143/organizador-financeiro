import { useMutation } from '@tanstack/react-query'

import { projectionsApi } from '../api/projections'

export function useSimulation() {
  return useMutation({ mutationFn: projectionsApi.simulate })
}