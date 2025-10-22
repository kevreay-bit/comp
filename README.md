# comp

This repository contains tooling to help determine whether ticket availability
endpoints require authentication and to provide reusable login-enabled scraping
sessions.  Because this execution environment does not provide private browsing
capabilities or access to the public internet, manual verification of each site
still needs to be performed outside the sandbox.  The automation added here is
structured so that it can reuse authenticated sessions when credentials are
present and to degrade gracefully when secrets are absent.

## Configuration

Ticket sites are described in `config/sites.json`.  Each entry includes the
human friendly name, the availability endpoint, and optional login metadata.
Secrets must always be sourced from environment variables – never from the
configuration file itself.

Two login strategies are supported:

* **Email/password** – describe the login URL, the names of the environment
  variables that store the email and password, and the form field names.  Extra
  form payload values (such as "remember me" flags) can be supplied via the
  `extra_payload` section.
* **Token header** – provide the environment variable that stores the token and
  optionally customise the header name and prefix.

The sample configuration uses placeholder endpoints from `example.com`; replace
these with the actual ticket provider URLs before running the checks.

## Checking login requirements

Run the CLI to inspect each configured availability endpoint:

```bash
python scripts/check_login_requirements.py config/sites.json --verbose
```

If credentials are available in the environment they are applied automatically
and the resulting session is reused for subsequent requests.  When credentials
are missing the tool logs a warning and continues anonymously so that the caller
can still observe the unauthenticated behaviour of the endpoint.

Use the `--json-output` flag to capture results in a machine-readable format.
The utility reports one of the following states per site:

* `accessible` – the endpoint returned a non-error response.
* `login_required` – the endpoint responded with HTTP 401 or 403.
* `client_error` – any other 4xx response.
* `server_error` – HTTP 5xx response codes.
* `unreachable` – networking errors such as DNS failures or timeouts.

Remember to conduct a one-off manual confirmation in a private browsing session
when network access is available to ensure the automation matches the provider's
actual behaviour.
