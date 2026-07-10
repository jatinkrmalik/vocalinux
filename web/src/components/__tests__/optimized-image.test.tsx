import React from 'react';
import { render, screen } from '@testing-library/react';
import { VocalinuxLogo } from '../optimized-image';

const mockImage = jest.fn();
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    mockImage(props);
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={props.src} alt={props.alt} width={props.width} height={props.height} />;
  },
}));

describe('VocalinuxLogo', () => {
  beforeEach(() => {
    mockImage.mockClear();
  });

  it('renders logo with accessible alt text', () => {
    render(<VocalinuxLogo />);
    expect(screen.getByAltText('Vocalinux')).toBeInTheDocument();
  });

  it('uses PNG path with WebP picture source', () => {
    const { container } = render(<VocalinuxLogo width={64} height={64} />);
    expect(container.querySelector('source')).toHaveAttribute('type', 'image/webp');
    expect(mockImage).toHaveBeenCalledWith(
      expect.objectContaining({
        src: '/vocalinux.png',
        width: 64,
        height: 64,
      })
    );
  });

  it('forwards className and priority', () => {
    render(<VocalinuxLogo className="h-8 w-8" priority />);
    expect(mockImage).toHaveBeenCalledWith(
      expect.objectContaining({
        className: 'h-8 w-8',
        priority: true,
      })
    );
  });
});
