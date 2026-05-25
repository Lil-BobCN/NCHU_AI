# NCHU SSO Public Research Result

Date: 2026-05-14

## Public Evidence

- Public SSO documentation exists at `https://passport.nchu.edu.cn/API/Help/ssodoc.aspx`.
- The school SSO launch endpoint is `https://passport.nchu.edu.cn/loging.aspx`.
- Initiating authentication requires QueryString parameters:
  - `SiteID`: site id issued by authentication center.
  - `Timespan`: current date/time string.
  - `ReturnURL`: subsystem callback URL.
  - `SignText`: uppercase MD5 signature: `MD5(SiteID + Timespan + ReturnURL + Key)`.
- After login, the authentication center redirects back to `ReturnURL` with:
  - `SiteID`
  - `Timespan`
  - `EndTime`
  - `UID`: teacher format `工号@nchu.edu.cn`; student format `学号@stu.nchu.edu.cn`; lowercase letters.
  - `Sname`: user name.
  - `SignText`: uppercase MD5 signature: `MD5(SiteID + UID + Sname + Timespan + EndTime + Key)`.
- Logout uses `http://passport.nchu.edu.cn/logout.aspx`, and the authentication center requires a subsystem logout action URL.
- Public standard endpoints checked returned 404 or were not publicly exposed: `/cas/login`, `/oauth/authorize`, `/oauth2/authorize`, `/connect/authorize`, `/.well-known/openid-configuration`.
- `DataCenter.asmx` is publicly discoverable and documents SOAP/HTTP(S), XML/JSON, IP authorization, `SiteID`, and data APIs such as `PAASGetUserInfo`.

## Architecture Implication

For this school, the safest P0 path is not direct Casdoor/OIDC integration. Implement a FastAPI-side `NchuSsoAdapter` first, with secrets and issued identifiers stored in environment variables.

Casdoor remains optional for future multi-identity-center use, but would likely require a custom provider/extension or an additional adapter because NCHU's public SSO flow is custom redirect + MD5 signature callback rather than standard OIDC/CAS.

## Data Still Required From School

- Issued `SiteID` for the AI counselor system.
- Secret `Key` used for MD5 signatures.
- Approved `ReturnURL` callback domain/path.
- Approved subsystem logout action URL.
- Whether `Timespan`/`EndTime` format and clock skew rules are exactly as public doc implies.
- Test account or test SSO environment.
- Whether the production server IP must be whitelisted.
- If user profile enrichment is needed: DataCenter/API authorization, allowed methods, IP whitelist, field dictionary, and rate/security requirements.
