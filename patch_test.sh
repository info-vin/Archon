sed -i -e "/expect(await screen.findByRole('option', { name: 'Alice Johnson' })).toBeInTheDocument();/i \\
    fireEvent.click(screen.getByRole('tab', { name: 'Assignment & Automation' }));" enduser-ui-fe/src/pages/DashboardPage.test.tsx
