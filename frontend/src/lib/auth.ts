import { useMsal } from '@azure/msal-react'

export function useAuthToken() {
  const { instance, accounts } = useMsal()

  const getToken = async (): Promise<string> => {
    const silentRequest = {
      scopes: [import.meta.env.VITE_AZURE_BACKEND_SCOPE],
      account: accounts[0],
    }
    try {
      const result = await instance.acquireTokenSilent(silentRequest)
      return result.accessToken
    } catch {
      const result = await instance.acquireTokenPopup({
        scopes: [import.meta.env.VITE_AZURE_BACKEND_SCOPE],
      })
      return result.accessToken
    }
  }

  return { getToken }
}
