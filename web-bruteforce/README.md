# Web brute-force practice

Four small exercises live on the local portal. Start at
`http://127.0.0.1:8080/`, without a supplied challenge username or login URL.
Use `labctl labs --track BF` for titles and `labctl hints BF-01` for a clue.
The pages use one plain template; the exercise is observing the requests.

1. **Discover.** Inspect `robots.txt`, then use the small directory wordlist.
   Robots exclusions are public clues, not access control, and do not list every
   page. Follow links from discovered directories to their sign-in forms.

   ```sh
   curl http://127.0.0.1:8080/robots.txt
   gobuster dir -u http://127.0.0.1:8080/ -w web-bruteforce/wordlists/paths.txt --add-slash -t 2
   ```

2. **Inspect.** Open View Source and DevTools. Compare visible labels, input
   names, JavaScript, and the submitted request in the Network tab. The visible
   word `Username` does not guarantee that the server accepts a field named
   `Username`: request keys can be case-sensitive.

3. **Recover the account.** Some pages leave a directory value in source.
   Base64 is reversible encoding; decode it. MD5 is a one-way hash; hash
   candidates from `wordlists/usernames.txt` and compare them with the leaked
   digest. You cannot decode a hash. Other exercises require online username
   enumeration instead of a source clue.

4. **Read errors as evidence.** Keep one input constant and change the other.
   Start with an intentionally invalid account and a wrong password. Do not
   infer success from HTTP 200: these logins return 200 for failures too.

   | Message | Username-first checker | Shared-password-first checker |
   | --- | --- | --- |
   | `incorrect username or password` | A generic failure does not identify the wrong field | A generic failure does not identify the wrong field |
   | `incorrect username` | Username unknown; password was not checked | Shared password passed; username unknown |
   | `incorrect password` | Username exists; password wrong | Shared password wrong; username was not checked |

   Those conclusions depend on the actual validation order. One exercise checks
   a shared password first on purpose; do not assume real applications do this.
   A generic message alone also does not prove an application resists timing
   attacks or repeated password guesses.

5. **Test the password list.** First reproduce one request manually. Set the
   following values to the path and username you discovered, then use the
   verified request field names. Stop when the page actually shows success.

   ```sh
   LAB_LOGIN_PATH='/replace-with-discovered-login-path'
   LAB_USERNAME='replace-with-recovered-username'
   hydra -l "$LAB_USERNAME" -P web-bruteforce/wordlists/passwords.txt -s 8080 -t 1 -f \
     127.0.0.1 http-post-form "${LAB_LOGIN_PATH}:username=^USER^&password=^PASS^:S=Login successful"
   ```

   For an enumeration exercise, first record the username or shared-password
   candidate confirmed by the response. That intermediate finding is not a
   successful login. Complete the second credential search before submitting.

6. **Submit and explain.** A successful POST shows the flag and a short lesson.
   Submit it to its `BF-xx` challenge with `labctl submit BF-01` (or the matching
   ID). Record the evidence for the endpoint, field names, recovered username,
   and what each failure told you. The wordlists contain only practice
   candidates; no entry is labelled as the correct credential.
