import asyncio

import httpx
import pytest

from codemodder.registry import load_registered_codemods

registry = load_registered_codemods()


async def visit_url(client, url):
    try:
        response = await client.get(url)
        return url, response.status_code
    except httpx.RequestError:
        return url, None


@pytest.mark.asyncio
async def check_accessible_urls(urls):
    async with httpx.AsyncClient() as client:
        tasks = [visit_url(client, url) for url in urls]
        results = await asyncio.gather(*tasks)

    if failures := [
        (url, status) for url, status in results if status not in (200, 301, 302)
    ]:
        if failures:
            failure_messages = [f"{url}: status={status}" for url, status in failures]
            pytest.fail(
                "Update the following URLs because they are not accessible:\n{}".format(
                    "\n".join(failure_messages)
                )
            )


@pytest.mark.asyncio
async def test_codemod_reference_urls():
    urls = [
        ref.url for codemod in registry.codemods for ref in codemod._metadata.references
    ]
    await check_accessible_urls(urls)


@pytest.mark.asyncio
async def test_tool_rules_urls():
    urls = [
        rule.url
        for codemod in registry.codemods
        if (tool := codemod._metadata.tool)
        for rule in tool.rules
        if rule.url
    ]
    await check_accessible_urls(urls)
