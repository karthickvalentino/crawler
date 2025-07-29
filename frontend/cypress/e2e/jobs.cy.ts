describe('Jobs Page', () => {
  beforeEach(() => {
    cy.intercept('GET', '/api/jobs*', { fixture: 'jobs.json' }).as('getJobs');
    cy.intercept('POST', '/start-crawler', {
      statusCode: 202,
      body: { id: 'new_job_id' },
    }).as('startCrawler');
  });

  it('should display the jobs page and create a new job', () => {
    cy.visit('/jobs');
    cy.wait('@getJobs');

    cy.contains('h1', 'Jobs');

    cy.contains('button', 'Create Job').click();

    cy.get('input[id=domain]').type('example.com');
    cy.get('input[id=depth]').type('1');

    cy.contains('button', 'Start Crawling').click();

    cy.wait('@startCrawler');
    cy.wait('@getJobs');

    cy.contains('td', 'fixture.com');
  });
});
