import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CreateJobForm } from './CreateJobForm';
import { startCrawler } from '@/services/api';

jest.mock('@/services/api');

test('renders CreateJobForm and submits', async () => {
  const handleJobCreated = jest.fn();
  render(<CreateJobForm onJobCreated={handleJobCreated} />);
  
  fireEvent.click(screen.getByText('Create Job'));
  
  fireEvent.change(screen.getByLabelText('Domain'), { target: { value: 'example.com' } });
  fireEvent.change(screen.getByLabelText('Depth'), { target: { value: '2' } });
  
  fireEvent.click(screen.getByText('Start Crawling'));
  
  await waitFor(() => {
    expect(startCrawler).toHaveBeenCalledWith('example.com', 2);
    expect(handleJobCreated).toHaveBeenCalled();
  });
});
