import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Box,
  VStack,
  HStack,
  Flex,
  Divider,
  Avatar,
  Text,
  Progress,
  Button,
  Heading,
  Icon,
  Tooltip,
  Alert,
  AlertIcon,
} from "@chakra-ui/react";
import { useAuthContext } from "../hooks/useAuthContext";
import { useLogout } from "../hooks/useLogout";
import { FaImages, FaChartBar } from "react-icons/fa";
import { MdStorage } from "react-icons/md";
import { VscSignOut } from "react-icons/vsc";

function Sidebar(props) {
  const { usedStorage } = props;
  const { user } = useAuthContext();
  const { logout } = useLogout();
  const [error, setError] = useState(null);

  const handleLogout = () => {
    logout();
  };

  return (
    <Flex
      direction="column"
      w="300px"
      h="100vh"
      p="5"
      borderRight="1px solid"
      borderColor="gray.200"
      justifyContent="space-between"
      bg="gray.50"
      color="gray.700"
      boxShadow="md"
    >
      <VStack align="start" spacing="6">
        {/* App Branding */}
        <Flex align="center">
          <Heading size="lg" color="teal.500">
            KotKit
          </Heading>
        </Flex>
        <Divider />

        {/* User Info */}
        <HStack spacing="4" w="100%">
          <Avatar
            size="lg"
            name={user.username}
            src="/path/to/user/avatar.png"
          />
          <VStack align="start" spacing="1">
            <Text fontSize="lg" fontWeight="bold">
              {user.username}
            </Text>
            <Text fontSize="sm" color="gray.500">
              {user.email}
            </Text>
          </VStack>
        </HStack>
        <Divider />

        {/* Navigation Links */}
        <VStack align="start" spacing="4" w="100%">
          <Link to="/" style={{ display: "block", width: "100%" }}>
            <Box
              as={Flex}
              align="center"
              p="3"
              borderRadius="md"
              _hover={{ bg: "teal.100" }}
            >
              <Icon as={FaImages} boxSize={5} color="teal.500" mr="3" />
              <Text fontSize="md">Dashboard</Text>
            </Box>
          </Link>
        </VStack>
      </VStack>

      {/* Storage Info */}
      {error && (
        <Alert status="error" w="100%">
          <AlertIcon />
          {error}
        </Alert>
      )}
      {usedStorage && (
        <VStack align="start" spacing="6" w="100%">
          <HStack w="100%">
            <Icon as={MdStorage} boxSize={5} color="blue.400" mr="3" />
            <Tooltip
              label={`Available Space: ${usedStorage.available_space_mb} MB out of ${usedStorage.storage_limit_mb} MB`}
              aria-label="Available Space Tooltip"
              placement="top"
            >
              <Progress
                colorScheme="blue"
                size="sm"
                value={
                  (usedStorage.available_space_mb /
                    usedStorage.storage_limit_mb) *
                  100
                }
                w="full"
                borderRadius="md"
              />
            </Tooltip>
          </HStack>
          <HStack w="100%">
            <Icon as={FaChartBar} boxSize={5} color="green.400" mr="3" />
            <Tooltip
              label={`Storage Usage: ${usedStorage.usage_percentage}%`}
              aria-label="Storage Usage Tooltip"
              placement="top"
            >
              <Progress
                colorScheme="green"
                size="sm"
                value={usedStorage.usage_percentage}
                w="full"
                borderRadius="md"
              />
            </Tooltip>
          </HStack>
        </VStack>
      )}

      {/* Logout Button */}
      <VStack align="start" spacing="6" w="100%">
        <Button
          leftIcon={<VscSignOut />}
          bg="teal.500"
          color="white"
          _hover={{ bg: "teal.400" }}
          onClick={handleLogout}
          w="full"
        >
          Sign Out
        </Button>
      </VStack>
    </Flex>
  );
}

export default Sidebar;
