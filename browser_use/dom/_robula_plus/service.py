import re
from typing import Dict, List, Optional

from playwright.async_api import ElementHandle, JSHandle, Page


class RobulaPlusOptions:
	"""
	Options for configuring the Robula Plus algorithm.

	default values:

	@param `attribute_prioritization_list = ['name', 'class', 'title', 'alt', 'value']`
	@param `attribute_blacklist = ['href', 'src', 'onclick', 'onload', 'tabindex', 'width', 'height', 'style', 'size', 'maxlength']`
	"""

	def __init__(
		self,
		attribute_prioritization_list: Optional[List[str]] = None,
		attribute_blacklist: Optional[List[str]] = None,
	):
		self.attribute_prioritization_list: List[str] = attribute_prioritization_list or [
			'name',
			# 'class',
			'title',
			'alt',
			'value',
		]
		self.attribute_blacklist: List[str] = attribute_blacklist or [
			'href',
			'class',
			'src',
			'onclick',
			'onload',
			'tabindex',
			'width',
			'height',
			'style',
			'size',
			'maxlength',
		]


class XPath:
	"""A class representing an XPath expression."""

	def __init__(self, value: str) -> None:
		self.value: str = value

	def get_value(self) -> str:
		return self.value

	def starts_with(self, prefix: str) -> bool:
		return self.value.startswith(prefix)

	def substring(self, start: int) -> str:
		return self.value[start:]

	def head_has_any_predicates(self) -> bool:
		return '[' in self.value.split('/')[2]

	def head_has_position_predicate(self) -> bool:
		head = self.value.split('/')[2]
		return 'position()' in head or 'last()' in head or bool(re.search(r'\[\d+\]', head))

	def head_has_text_predicate(self) -> bool:
		return 'text()' in self.value.split('/')[2]

	def add_predicate_to_head(self, predicate: str) -> None:
		parts = self.value.split('/')
		parts[2] += predicate
		self.value = '/'.join(parts)

	def get_length(self) -> int:
		return len([part for part in self.value.split('/') if part])


class RobulaPlus:
	"""
	Main class implementing the Robula Plus algorithm.
	"""

	def __init__(self, options: Optional[RobulaPlusOptions] = None) -> None:
		if options is None:
			options = RobulaPlusOptions()
		self.attribute_prioritization_list: List[str] = options.attribute_prioritization_list
		self.attribute_blacklist: List[str] = options.attribute_blacklist

	async def get_robust_xpath(self, element: ElementHandle, page: Page) -> str:
		"""Returns an optimized robust XPath locator string."""
		is_contained = await page.evaluate('(element) => document.body.contains(element)', element)
		if not is_contained:
			raise ValueError('Document does not contain given element!')

		xpath_list: List[XPath] = [XPath('//*')]
		while xpath_list:
			xpath = xpath_list.pop(0)
			print('Trying:', xpath.value)
			temp: List[XPath] = []

			# Apply transformations
			temp.extend(await self.transf_convert_star(xpath, element))
			temp.extend(await self.transf_add_id(xpath, element))
			temp.extend(await self.transf_add_text(xpath, element))
			temp.extend(await self.transf_add_attribute(xpath, element))
			temp.extend(await self.transf_add_attribute_set(xpath, element))
			temp.extend(await self.transf_add_position(xpath, element))
			temp.extend(await self.transf_add_level(xpath, element))

			# Remove duplicates
			temp = list({x.get_value(): x for x in temp}.values())

			for x in temp:
				if await self.uniquely_locate(x.get_value(), element, page):
					return x.get_value()
				xpath_list.append(x)

		raise RuntimeError('Failed to generate robust XPath')

	async def uniquely_locate(self, xpath: str, element: ElementHandle, page: Page) -> bool:
		"""Determines whether an XPath uniquely identifies the given element."""
		elements = await page.query_selector_all(xpath)
		if len(elements) != 1:
			return False

		# Compare elements using isSameElement
		try:
			return await elements[0].evaluate('(el, other) => el === other', element)
		except Exception:
			return False

	async def get_element_by_xpath(self, xpath: str, page: Page) -> Optional[ElementHandle]:
		"""Returns the element located by the given XPath."""
		return await page.query_selector(xpath)

	async def get_ancestor(self, element: ElementHandle, index: int) -> ElementHandle | JSHandle:
		"""Gets the ancestor element at the specified index."""
		current = element
		for _ in range(index):
			parent = await current.evaluate_handle('el => el.parentElement')
			if not parent:
				raise ValueError('Ancestor index out of bounds')
			current = parent
		return current

	async def get_ancestor_count(self, element: ElementHandle) -> int:
		"""Gets the number of ancestors for the element."""
		count = 0
		current = element
		while True:
			try:
				parent = await current.evaluate_handle('el => el.parentElement')
				if not parent or await parent.evaluate('el => el === null'):
					break
				count += 1
				current = ElementHandle(parent)
			except Exception:
				break
		return count

	async def transf_convert_star(self, xpath: XPath, element: ElementHandle) -> List[XPath]:
		"""Transforms * to specific tag name."""
		output: List[XPath] = []
		ancestor = await self.get_ancestor(element, xpath.get_length() - 1)
		if xpath.starts_with('//*'):
			tag_name = await ancestor.evaluate('el => el.tagName.toLowerCase()')
			output.append(XPath('//' + tag_name + xpath.substring(3)))
		return output

	async def transf_add_id(self, xpath: XPath, element: ElementHandle) -> List[XPath]:
		"""Adds ID predicate if available."""
		output: List[XPath] = []
		ancestor = await self.get_ancestor(element, xpath.get_length() - 1)
		element_id = await ancestor.evaluate('el => el.id')
		if element_id and not xpath.head_has_any_predicates():
			new_xpath = XPath(xpath.get_value())
			new_xpath.add_predicate_to_head(f"[@id='{element_id}']")
			output.append(new_xpath)
		return output

	async def transf_add_text(self, xpath: XPath, element: ElementHandle) -> List[XPath]:
		"""Adds text predicate if available."""
		output: List[XPath] = []
		ancestor = await self.get_ancestor(element, xpath.get_length() - 1)
		text_content = await ancestor.evaluate('el => el.textContent')
		if (
			text_content
			and not xpath.head_has_position_predicate()
			and not xpath.head_has_text_predicate()
		):
			new_xpath = XPath(xpath.get_value())
			new_xpath.add_predicate_to_head(f"[contains(text(),'{text_content}')]")
			output.append(new_xpath)
		return output

	async def transf_add_attribute(self, xpath: XPath, element: ElementHandle) -> List[XPath]:
		"""Adds attribute predicates."""
		output: List[XPath] = []
		if not xpath.head_has_any_predicates():
			ancestor = await self.get_ancestor(element, xpath.get_length() - 1)
			attributes = await ancestor.evaluate("""el => {
                const attrs = {};
                for (const attr of el.attributes) {
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            }""")

			# Add priority attributes first
			for attr_name in self.attribute_prioritization_list:
				if attr_name in attributes:
					new_xpath = XPath(xpath.get_value())
					new_xpath.add_predicate_to_head(f"[@{attr_name}='{attributes[attr_name]}']")
					output.append(new_xpath)

			# Add remaining non-blacklisted attributes
			for attr_name, attr_value in attributes.items():
				if (
					attr_name not in self.attribute_blacklist
					and attr_name not in self.attribute_prioritization_list
				):
					new_xpath = XPath(xpath.get_value())
					new_xpath.add_predicate_to_head(f"[@{attr_name}='{attr_value}']")
					output.append(new_xpath)

		return output

	async def transf_add_position(self, xpath: XPath, element: ElementHandle) -> List[XPath]:
		"""Adds position predicate."""
		output: List[XPath] = []
		if not xpath.head_has_position_predicate():
			ancestor = await self.get_ancestor(element, xpath.get_length() - 1)
			position = await ancestor.evaluate(
				"""(el, isStarXPath) => {
                const parent = el.parentNode;
                if (isStarXPath) {
                    return Array.from(parent.children).indexOf(el) + 1;
                } else {
                    let pos = 1;
                    for (const child of parent.children) {
                        if (el === child) break;
                        if (el.tagName === child.tagName) pos++;
                    }
                    return pos;
                }
            }""",
				xpath.starts_with('//*'),
			)
			new_xpath = XPath(xpath.get_value())
			new_xpath.add_predicate_to_head(f'[{position}]')
			output.append(new_xpath)
		return output

	async def transf_add_level(self, xpath: XPath, element: ElementHandle) -> List[XPath]:
		"""Adds level transformation."""
		output: List[XPath] = []
		ancestor_count = await self.get_ancestor_count(element)
		if xpath.get_length() - 1 < ancestor_count:
			output.append(XPath('//*' + xpath.substring(1)))
		return output

	async def transf_add_attribute_set(self, xpath: XPath, element: ElementHandle) -> List[XPath]:
		"""Adds attribute set predicates."""
		output: List[XPath] = []
		if not xpath.head_has_any_predicates():
			ancestor = await self.get_ancestor(element, xpath.get_length() - 1)
			attributes = await ancestor.evaluate("""el => {
                return Array.from(el.attributes)
                    .map(attr => ({name: attr.name, value: attr.value}));
            }""")

			# Filter out blacklisted attributes
			attributes = [
				attr for attr in attributes if attr['name'] not in self.attribute_blacklist
			]

			# Generate power set of attributes
			power_set = self._generate_power_set(attributes)

			# Filter and sort attribute sets
			power_set = [s for s in power_set if len(s) >= 2]
			for attr_set in power_set:
				attr_set.sort(key=lambda x: self._get_attribute_priority(x['name']))

			# Create XPath predicates
			for attr_set in power_set:
				predicate = self._create_attribute_set_predicate(attr_set)
				new_xpath = XPath(xpath.get_value())
				new_xpath.add_predicate_to_head(predicate)
				output.append(new_xpath)

		return output

	def _generate_power_set(self, attributes: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
		"""Generates power set of attributes."""
		result = [[]]
		for attr in attributes:
			result.extend([subset + [attr] for subset in result])
		return result

	def _get_attribute_priority(self, attr_name: str) -> int:
		"""Gets the priority of an attribute."""
		try:
			return self.attribute_prioritization_list.index(attr_name)
		except ValueError:
			return len(self.attribute_prioritization_list)

	def _create_attribute_set_predicate(self, attr_set: List[Dict[str, str]]) -> str:
		"""Creates an XPath predicate from an attribute set."""
		conditions = [f"@{attr['name']}='{attr['value']}'" for attr in attr_set]
		return f"[{' and '.join(conditions)}]"
