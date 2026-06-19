declare module "react-plotly.js" {
  import type { ComponentType } from "react";

  type PlotProps = {
    data: Array<Record<string, unknown>>;
    layout?: Record<string, unknown>;
    config?: Record<string, unknown>;
    className?: string;
    style?: Record<string, string | number>;
  };

  const Plot: ComponentType<PlotProps>;
  export default Plot;
}
