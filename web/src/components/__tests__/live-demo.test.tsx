import React from "react";
import { render, screen } from "@testing-library/react";
import { LiveDemo } from "../live-demo";

describe("LiveDemo unsupported browser state", () => {
  const originalSpeechRecognition = window.SpeechRecognition;
  const originalWebkitSpeechRecognition = window.webkitSpeechRecognition;

  beforeEach(() => {
    Object.defineProperty(window, "SpeechRecognition", {
      configurable: true,
      writable: true,
      value: undefined,
    });
    Object.defineProperty(window, "webkitSpeechRecognition", {
      configurable: true,
      writable: true,
      value: undefined,
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "SpeechRecognition", {
      configurable: true,
      writable: true,
      value: originalSpeechRecognition,
    });
    Object.defineProperty(window, "webkitSpeechRecognition", {
      configurable: true,
      writable: true,
      value: originalWebkitSpeechRecognition,
    });
  });

  it("explains missing speech recognition support and links to compatibility references", async () => {
    render(<LiveDemo />);

    expect(
      await screen.findByText("Browser Speech Demo Not Available"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/does not support the SpeechRecognition API/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Chrome")).toBeInTheDocument();
    expect(screen.getByText("Edge")).toBeInTheDocument();
    expect(screen.getByText("Safari")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "MDN" })).toHaveAttribute(
      "href",
      "https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition",
    );
  });
});
