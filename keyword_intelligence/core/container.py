"""Dependency Injection / IoC Container for the application."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

from keyword_intelligence.core.exceptions import ConfigurationError

T = TypeVar("T")


class ServiceLifetime(Enum):
    """Lifetime of a registered service."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"


class ServiceContainer:
    """Inversion of Control (IoC) Container.

    Supports singleton and transient lifecycles, lazy initialization,
    and factory-based registration.
    """

    def __init__(self) -> None:
        """Initialize empty container."""
        # Stores factories: Type -> (ServiceLifetime, Callable[[], Any])
        self._factories: dict[type, tuple[ServiceLifetime, Callable[[], Any]]] = {}
        # Stores instantiated singletons: Type -> Instance
        self._instances: dict[type, Any] = {}

    def register(
        self,
        interface: type[T],
        factory: Callable[[], T],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    ) -> None:
        """Register a service factory.

        Args:
            interface: The type/interface to register.
            factory: A callable that returns an instance of the type.
            lifetime: ServiceLifetime.SINGLETON or ServiceLifetime.TRANSIENT.
        """
        self._factories[interface] = (lifetime, factory)

    def register_instance(self, interface: type[T], instance: T) -> None:
        """Register an existing instance as a singleton.

        Args:
            interface: The type/interface to register.
            instance: The concrete instance.
        """
        self._factories[interface] = (ServiceLifetime.SINGLETON, lambda: instance)
        self._instances[interface] = instance

    def resolve(self, interface: type[T]) -> T:
        """Resolve an instance for the given interface.

        Args:
            interface: The requested type/interface.

        Returns:
            An instance of the requested type.

        Raises:
            AppConfigurationError: If the type is not registered.
        """
        if interface not in self._factories:
            raise ConfigurationError(
                f"No service registered for interface: {interface.__name__}"
            )

        lifetime, factory = self._factories[interface]

        if lifetime == ServiceLifetime.SINGLETON:
            if interface not in self._instances:
                # Lazy initialization on first resolve
                self._instances[interface] = factory()
            return self._instances[interface]

        # Transient: always call factory
        return factory()

    def clear(self) -> None:
        """Clear all registrations and instances (useful for testing)."""
        self._factories.clear()
        self._instances.clear()


# Global container instance
container = ServiceContainer()
