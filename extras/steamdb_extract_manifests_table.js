// Put this in the devtools console on a page like <https://steamdb.info/depot/368341/manifests/>
for (method in console) {
  if (console[method]._restore != null) {
    console[method]._restore();
  }
}
console.log(
  Array.from(document.querySelectorAll('#manifests table > tbody > tr'))
    .map((tr) => {
      let tds = tr.querySelectorAll('td');
      return tds.length > 0
        ? `- \{ id: "${tds[2].innerText}", seen: ${Math.floor(
            new Date(tds[1].dataset.time).getTime() / 1000,
          )} \}`
        : null;
    })
    .join('\n'),
);
