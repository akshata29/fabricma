import { AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react'
import { useMsal } from '@azure/msal-react'
import { AppShell } from '@/components/shell/AppShell'

function SignInPage() {
  const { instance } = useMsal()
  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <h1 className="text-2xl font-bold text-foreground">FabricMA</h1>
        <p className="text-muted-foreground">Meridian Supply Co. Multi-Agent Analytics</p>
        <button
          onClick={() => instance.loginPopup()}
          className="rounded-md bg-primary px-6 py-2 text-primary-foreground hover:opacity-90 transition-opacity"
        >
          Sign in with Microsoft
        </button>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <>
      <AuthenticatedTemplate>
        <AppShell />
      </AuthenticatedTemplate>
      <UnauthenticatedTemplate>
        <SignInPage />
      </UnauthenticatedTemplate>
    </>
  )
}
