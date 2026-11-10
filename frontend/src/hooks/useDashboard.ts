import { useQuery } from '@tanstack/react-query'

import { dashboardApi } from '../api/dashboard'

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'], 
    queryFn: dashboardApi.get,  
    retry: false, 
    staleTime: 30_000,
    placeholderData: (previousData) => previousData,
  })
}
