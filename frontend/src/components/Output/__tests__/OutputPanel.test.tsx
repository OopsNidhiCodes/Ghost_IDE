import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { OutputPanel } from '../OutputPanel';
import { useAppStore } from '../../../store/useAppStore';

// Mock the store
vi.mock('../../../store/useAppStore');

const mockStore = {
  executionResult: null,
  isExecuting: false,
  setExecutionResult: vi.fn(),
  executionHistory: [],
  addToExecutionHistory: vi.fn(),
  clearExecutionHistory: vi.fn(),
};

describe('OutputPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useAppStore as any).mockReturnValue(mockStore);
  });

  it('renders empty state correctly', () => {
    render(<OutputPanel />);
    
    expect(screen.getByText('Output')).toBeInTheDocument();
    expect(screen.getByText('The spirits await your code...')).toBeInTheDocument();
    expect(screen.getByText('Ready')).toBeInTheDocument();
  });

  it('shows executing state with spinner', () => {
    (useAppStore as any).mockReturnValue({
      ...mockStore,
      isExecuting: true,
    });

    render(<OutputPanel />);
    
    expect(screen.getByText('Executing...')).toBeInTheDocument();
    expect(screen.getByText('Executing code in the spirit realm...')).toBeInTheDocument();
  });

  it('displays successful execution results', () => {
    const successResult = {
      stdout: 'Hello, World!\nProgram completed successfully',
      stderr: '',
      exitCode: 0,
      executionTime: 1250,
    };

    (useAppStore as any).mockReturnValue({
      ...mockStore,
      executionResult: successResult,
    });

    render(<OutputPanel />);
    
    expect(screen.getByText('Success')).toBeInTheDocument();
    expect(screen.getByText(/Hello, World!/)).toBeInTheDocument();
    expect(screen.getByText(/Execution Time:/)).toBeInTheDocument();
    expect(screen.getByText('📤 STDOUT')).toBeInTheDocument();
  });

  it('displays error execution results with stderr', () => {
    const errorResult = {
      stdout: '',
      stderr: 'Traceback (most recent call last):\n  File "test.py", line 5, in <module>\n    print(undefined_variable)\nNameError: name \'undefined_variable\' is not defined',
      exitCode: 1,
      executionTime: 500,
    };

    (useAppStore as any).mockReturnValue({
      ...mockStore,
      executionResult: errorResult,
    });

    render(<OutputPanel />);
    
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('⚠️ STDERR')).toBeInTheDocument();
    expect(screen.getByText(/NameError: name 'undefined_variable' is not defined/)).toBeInTheDocument();
    expect(screen.getByText(/Execution Time:/)).toBeInTheDocument();
  });

  it('formats execution time correctly', () => {
    const fastResult = {
      stdout: 'Fast execution',
      stderr: '',
      exitCode: 0,
      executionTime: 150,
    };

    (useAppStore as any).mockReturnValue({
      ...mockStore,
      executionResult: fastResult,
    });

    const { rerender } = render(<OutputPanel />);
    expect(screen.getByText(/Execution Time:/)).toBeInTheDocument();
    expect(screen.getByText((_content, element) => {
      return element?.textContent === 'Execution Time: 150ms';
    })).toBeInTheDocument();

    const slowResult = {
      stdout: 'Slow execution',
      stderr: '',
      exitCode: 0,
      executionTime: 2500,
    };

    (useAppStore as any).mockReturnValue({
      ...mockStore,
      executionResult: slowResult,
    });

    rerender(<OutputPanel />);
    expect(screen.getByText((_content, element) => {
      return element?.textContent === 'Execution Time: 2.50s';
    })).toBeInTheDocument();
  });

  it('clears output when clear button is clicked', () => {
    const result = {
      stdout: 'Some output',
      stderr: '',
      exitCode: 0,
      executionTime: 1000,
    };

    (useAppStore as any).mockReturnValue({
      ...mockStore,
      executionResult: result,
    });

    render(<OutputPanel />);
    
    const clearButton = screen.getByTitle('Clear output');
    fireEvent.click(clearButton);
    
    expect(mockStore.setExecutionResult).toHaveBeenCalledWith(null);
  });

  it('shows execution history when available', () => {
    const historyResults = [
      {
        stdout: 'First execution',
        stderr: '',
        exitCode: 0,
        executionTime: 1000,
      },
      {
        stdout: '',
        stderr: 'Second execution error',
        exitCode: 1,
        executionTime: 500,
      },
    ];

    (useAppStore as any).mockReturnValue({
      ...mockStore,
      executionHistory: historyResults,
    });

    render(<OutputPanel />);
    
    expect(screen.getByText(/History \(2\)/)).toBeInTheDocument();
  });

  it('toggles history panel visibility', () => {
    const historyResults = [
      {
        stdout: 'Test output',
        stderr: '',
        exitCode: 0,
        executionTime: 1000,
      },
    ];

    (useAppStore as any).mockReturnValue({
      ...mockStore,
      executionHistory: historyResults,
    });

    render(<OutputPanel />);
    
    const historyButton = screen.getByText(/History \(1\)/);
    fireEvent.click(historyButton);
    
    expect(screen.getByText('Execution History')).toBeInTheDocument();
    expect(screen.getByText(/Test output/)).toBeInTheDocument();
  });

  it('loads execution result from history when clicked', () => {
    const historyResult = {
      stdout: 'Historical output',
      stderr: '',
      exitCode: 0,
      executionTime: 1500,
    };

    (useAppStore as any).mockReturnValue({
      ...mockStore,
      executionHistory: [historyResult],
    });

    render(<OutputPanel />);
    
    // Open history
    const historyButton = screen.getByText(/History \(1\)/);
    fireEvent.click(historyButton);
    
    // Click on history item
    const historyItem = screen.getByText(/Historical output/);
    fireEvent.click(historyItem.closest('div')!);
    
    expect(mockStore.setExecutionResult).toHaveBeenCalledWith(historyResult);
  });

  it('parses error messages with line numbers', () => {
    const errorWithLineNumbers = {
      stdout: '',
      stderr: 'File "test.py", line 10, in <module>\n    syntax error here\nSyntaxError: invalid syntax',
      exitCode: 1,
      executionTime: 200,
    };

    (useAppStore as any).mockReturnValue({
      ...mockStore,
      executionResult: errorWithLineNumbers,
    });

    render(<OutputPanel />);
    
    // Check that line number is highlighted
    const errorLine = screen.getByText(/File "test.py", line 10/);
    expect(errorLine).toHaveClass('text-red-400');
  });

  it('shows line count for output sections', () => {
    const multiLineResult = {
      stdout: 'Line 1\nLine 2\nLine 3\nLine 4',
      stderr: 'Error line 1\nError line 2',
      exitCode: 1,
      executionTime: 800,
    };

    (useAppStore as any).mockReturnValue({
      ...mockStore,
      executionResult: multiLineResult,
    });

    render(<OutputPanel />);
    
    expect(screen.getByText('(3 lines)')).toBeInTheDocument(); // stdout lines
    expect(screen.getByText('(1 lines)')).toBeInTheDocument(); // stderr lines
  });

  it('disables clear button when no output', () => {
    render(<OutputPanel />);
    
    const clearButton = screen.getByTitle('Clear output');
    expect(clearButton).toBeDisabled();
  });

  it('shows current execution time while executing', () => {
    (useAppStore as any).mockReturnValue({
      ...mockStore,
      isExecuting: true,
    });

    render(<OutputPanel />);
    
    expect(screen.getByText('Executing...')).toBeInTheDocument();
    expect(screen.getByText(/⏱️/)).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<OutputPanel className="custom-class" />);
    
    expect(container.firstChild).toHaveClass('custom-class');
  });
});