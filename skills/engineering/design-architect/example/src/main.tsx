import { StrictMode, type CSSProperties, type ReactNode, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ThemeProvider,
  type ThemeId,
  type ThemeModule,
  useTheme,
} from "./generated/themes/ThemeContext";
import "./styles.css";

type ButtonVariant = ThemeModule["buttonRecipe"] extends Record<infer Key, unknown>
  ? Key
  : never;

type BadgeVariant = ThemeModule["badgeRecipe"] extends Record<infer Key, unknown>
  ? Key
  : never;

type Recipe = Record<string, string | number>;

const buttonVariants: ButtonVariant[] = [
  "primary",
  "secondary",
  "selected",
  "dangerPrimary",
  "dangerSecondary",
];

const badgeVariants: BadgeVariant[] = [
  "info",
  "neutral",
  "success",
  "warning",
  "danger",
];

function recipeStyle(recipe: Recipe): CSSProperties {
  return recipe as CSSProperties;
}

function px(value: string | number | undefined) {
  return typeof value === "number" ? `${value}px` : value;
}

function App() {
  const { theme, themeId, setThemeId, themeOptions, cssVariables } = useTheme();

  return (
    <main
      className="app"
      style={{
        ...cssVariables,
        ...recipeStyle(theme.componentRecipe.page),
      }}
    >
      <header className="topbar" style={recipeStyle(theme.componentRecipe.header)}>
        <div>
          <p className="eyebrow">Generated styling showcase</p>
          <h1>Design Architect</h1>
        </div>
        <label className="theme-select">
          <span>Theme</span>
          <select
            value={themeId}
            onChange={(event) => setThemeId(event.target.value as ThemeId)}
          >
            {themeOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.name}
              </option>
            ))}
          </select>
        </label>
      </header>

      <section className="hero">
        <p className="eyebrow">{theme.designTheme.name}</p>
        <div className="hero-meta">
          <span>{theme.designTokens.typography.fontFamily}</span>
          <span>{theme.designTokens.borders.defaultWidth} borders</span>
          <span>{theme.designTokens.motion.hover}</span>
        </div>
      </section>

      <section className="layout-grid">
        <ShowcaseCard title="Buttons" description="Every generated button variant with hover, pressed, focus, and disabled states.">
          <div className="button-grid">
            {buttonVariants.map((variant) => (
              <ThemeButton key={variant} variant={variant} theme={theme}>
                {variant}
              </ThemeButton>
            ))}
            <ThemeButton variant="primary" theme={theme} disabled>
              disabled
            </ThemeButton>
          </div>
        </ShowcaseCard>

        <ShowcaseCard title="Inputs" description="Default, active, destructive, disabled, and selectable field states.">
          <div className="stack">
            <ThemeInput theme={theme} placeholder="Default input" />
            <ThemeInput theme={theme} placeholder="Focused input" forceActive />
            <ThemeInput theme={theme} placeholder="Destructive input" destructive />
            <ThemeInput theme={theme} placeholder="Disabled input" disabled />
          </div>
        </ShowcaseCard>

        <ShowcaseCard title="Badges" description="Generated label variants using badge tokens and borders.">
          <div className="badge-grid">
            {badgeVariants.map((variant) => (
              <span
                key={variant}
                className="badge"
                style={recipeStyle(theme.badgeRecipe[variant])}
              >
                {variant}
              </span>
            ))}
          </div>
        </ShowcaseCard>

        <ShowcaseCard title="Cards" description="Default and resource card recipes with generated spacing, radius, shadow, and border values.">
          <div className="card-pair">
            <div className="mini-card" style={recipeStyle(theme.cardRecipe.default)}>
              <strong>Default card</strong>
              <span>Surface, radius, shadow, and box border.</span>
            </div>
            <div className="mini-card" style={recipeStyle(theme.cardRecipe.resource)}>
              <strong>Resource card</strong>
              <span>Alternative generated card recipe.</span>
            </div>
          </div>
        </ShowcaseCard>

        <ShowcaseCard title="Tables" description="Header, row, and cell recipes with hover behavior.">
          <ThemeTable theme={theme} />
        </ShowcaseCard>

        <ShowcaseCard title="Overlays" description="Modal, drawer, and toast surfaces from generated overlay recipes.">
          <div className="overlay-grid">
            <div className="modal-demo" style={recipeStyle(theme.overlayRecipe.modal)}>
              <strong>Modal</strong>
              <span>Max width {theme.overlayRecipe.modal.maxWidth}px</span>
            </div>
            <div className="drawer-demo" style={recipeStyle(theme.overlayRecipe.drawer)}>
              <strong>Drawer</strong>
              <span>Anchor {theme.overlayRecipe.drawer.anchor}</span>
            </div>
            <div className="toast-demo" style={recipeStyle(theme.overlayRecipe.toast)}>
              <strong>Toast</strong>
              <span>Generated notification surface.</span>
            </div>
          </div>
        </ShowcaseCard>
      </section>

      <section className="wide-section">
        <ShowcaseCard title="Application shell" description="Generated layout metrics and active navigation colors.">
          <div className="shell-demo">
            <aside
              style={{
                background: theme.appShellRecipe.sidebarBackground,
                width: px(theme.appShellRecipe.sidebarWidth),
              }}
            >
              <span>Sidebar</span>
              <button
                style={{
                  background: theme.appShellRecipe.activeNavBackground,
                  color: theme.appShellRecipe.activeNavText,
                }}
              >
                Active item
              </button>
            </aside>
            <div style={{ background: theme.appShellRecipe.mainBackground }}>
              <div style={{ minHeight: px(theme.appShellRecipe.topNavHeight) }}>
                Top navigation
              </div>
              <p>Shell content uses generated background and navigation tokens.</p>
            </div>
          </div>
        </ShowcaseCard>

        <ShowcaseCard title="Token summary" description="Core generated token groups from the selected theme.">
          <div className="token-grid">
            {Object.entries(theme.designTokens.colors).map(([name, value]) => (
              <div key={name} className="token-row">
                <span className="swatch" style={{ background: value }} />
                <code>{name}</code>
                <span>{value}</span>
              </div>
            ))}
          </div>
        </ShowcaseCard>
      </section>

      <footer className="footer" style={recipeStyle(theme.componentRecipe.footer)}>
        <span>{theme.designTheme.name}</span>
        <span>{theme.designTheme.description}</span>
      </footer>
    </main>
  );
}

function ShowcaseCard({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  const { theme } = useTheme();
  return (
    <section className="showcase-card" style={recipeStyle(theme.cardRecipe.default)}>
      <div className="section-heading">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      {children}
    </section>
  );
}

function ThemeButton({
  variant,
  theme,
  children,
  disabled = false,
}: {
  variant: ButtonVariant;
  theme: ThemeModule;
  children: ReactNode;
  disabled?: boolean;
}) {
  const [state, setState] = useState<"idle" | "hover" | "active">("idle");
  const recipe = theme.buttonRecipe[variant];
  const stateStyle: CSSProperties =
    disabled
      ? {
          background: recipe.disabledBackground,
          color: recipe.disabledColor,
          cursor: "not-allowed",
        } as CSSProperties
      : state === "active"
        ? {
            background: recipe.activeBackground ?? recipe.hoverBackground ?? recipe.background,
            borderColor: recipe.activeBorderColor,
          } as CSSProperties
        : state === "hover"
          ? {
              background: recipe.hoverBackground ?? theme.designTokens.colors.hover,
              borderColor: recipe.hoverBorderColor,
            } as CSSProperties
          : {};

  return (
    <button
      disabled={disabled}
      className="theme-button"
      style={{ ...recipeStyle(recipe), ...stateStyle }}
      onMouseEnter={() => setState("hover")}
      onMouseLeave={() => setState("idle")}
      onMouseDown={() => setState("active")}
      onMouseUp={() => setState("hover")}
    >
      {children}
    </button>
  );
}

function ThemeInput({
  theme,
  placeholder,
  forceActive = false,
  destructive = false,
  disabled = false,
}: {
  theme: ThemeModule;
  placeholder: string;
  forceActive?: boolean;
  destructive?: boolean;
  disabled?: boolean;
}) {
  const [active, setActive] = useState(false);
  const recipe = theme.inputRecipe.default;
  const stateStyle: CSSProperties = disabled
    ? recipeStyle(theme.inputRecipe.disabled)
    : destructive
      ? recipeStyle(theme.inputRecipe.destructive)
      : active || forceActive
        ? recipeStyle(theme.inputRecipe.active)
        : {};

  return (
    <input
      className="theme-input"
      disabled={disabled}
      placeholder={placeholder}
      style={{ ...recipeStyle(recipe), ...stateStyle }}
      onFocus={() => setActive(true)}
      onBlur={() => setActive(false)}
    />
  );
}

function ThemeTable({ theme }: { theme: ThemeModule }) {
  const [hovered, setHovered] = useState<number | null>(null);
  const rows = [
    ["Primary", theme.designTokens.colors.primaryButton, "button"],
    ["Surface", theme.designTokens.colors.surface, "background"],
    ["Selected", theme.designTokens.colors.selectedButton, "state"],
  ];

  return (
    <table className="theme-table">
      <thead style={recipeStyle(theme.tableRecipe.header)}>
        <tr>
          <th style={recipeStyle(theme.tableRecipe.cell)}>Token</th>
          <th style={recipeStyle(theme.tableRecipe.cell)}>Value</th>
          <th style={recipeStyle(theme.tableRecipe.cell)}>Role</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => (
          <tr
            key={row[0]}
            style={{
              ...recipeStyle(theme.tableRecipe.row),
              background:
                hovered === index
                  ? theme.tableRecipe.row.hoverBackground
                  : "transparent",
            }}
            onMouseEnter={() => setHovered(index)}
            onMouseLeave={() => setHovered(null)}
          >
            {row.map((cell) => (
              <td key={cell} style={recipeStyle(theme.tableRecipe.cell)}>
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </StrictMode>,
);
