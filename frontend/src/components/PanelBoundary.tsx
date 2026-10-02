import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  label: string
}

interface State {
  error: string | null
}

/**
 * Keeps an optional panel from taking down the shell.
 *
 * The WebGL 3D view is the realistic failure case (a browser or VM without GPU support throws
 * while creating the context). PROJECT_SPEC.md §9 says the demo must always complete, so a failed
 * panel degrades to a labelled message instead of a blank page.
 */
export default class PanelBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: unknown): State {
    return { error: error instanceof Error ? error.message : 'Unknown rendering error' }
  }

  render() {
    if (this.state.error !== null) {
      return (
        <section className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-5">
          <h2 className="text-sm font-semibold text-amber-200">{this.props.label} unavailable</h2>
          <p className="mt-2 text-xs leading-relaxed text-amber-200/80">
            This panel could not render in this browser — usually a missing WebGL context. The rest of the
            shell is unaffected.
          </p>
          <p className="mt-2 font-mono text-[10px] text-amber-200/60">{this.state.error}</p>
        </section>
      )
    }

    return this.props.children
  }
}
